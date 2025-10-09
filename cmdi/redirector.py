import ctypes
import fcntl
import io
import os
import pty
import re
import sys
import termios
import time
from contextlib import contextmanager
from dataclasses import dataclass
from io import FileIO
from queue import Empty, Queue
from select import select
from threading import Thread
from typing import IO, Any, Generator, Optional, TextIO, Tuple, Union

from cmdi.lib import Pipe, Std


@dataclass
class _LowlevelRedirector:
    should_redirect: bool = False
    save: bool = False
    text: bool = False
    tty: bool = False
    mute: bool = False
    logfile: Optional[Union[io.StringIO, io.BytesIO]] = None
    original_std_fd: Optional[int] = None
    master_fd: Optional[int] = None
    master_file: Optional[IO] = None
    saved_std_fd: Optional[int] = None
    saved_std_file: Optional[IO] = None


@dataclass
class _HighlevelRedirector:
    file: Optional[Union[io.StringIO, io.BytesIO]] = None


libc = ctypes.CDLL(None)
c_stdout = ctypes.c_void_p.in_dll(libc, "stdout")
c_stderr = ctypes.c_void_p.in_dll(libc, "stderr")


def flush_c(stdtype: Std) -> None:
    if stdtype == Std.OUT:
        libc.fflush(c_stdout)
    else:
        libc.fflush(c_stderr)


def _setup_lowlevel_redirector(
    stdtype: Std,
) -> Tuple[Union[int, Any], int, FileIO, int, FileIO]:
    if stdtype == Std.OUT:
        stdfile = sys.stdout
    else:
        stdfile = sys.stderr

    # Save the original file descirptors stdout/stderr point to.
    original_stdfile_fd = stdfile.fileno()

    # Save a copy of the original file descriptors for stdout/stderr:
    # Data that is written to these will still appear in the users terminal.
    saved_stdfile_fd = os.dup(stdfile.fileno())

    # Create pseudo terminal reader, writer for stdout and stderr.
    # The slaves are able to write streams without loosing ANSI sequnces, that's why we
    # use them.
    pty_master_fd, pty_slave_fd = pty.openpty()

    # Configure pseudo-terminal writer to turn newlines from `/r/n` into `/n` for stdout.
    attrs = termios.tcgetattr(pty_slave_fd)
    attrs[1] = attrs[1] & (~termios.ONLCR) | termios.ONLRET  # type: ignore
    termios.tcsetattr(pty_slave_fd, termios.TCSANOW, attrs)

    # Open original stdfile.
    saved_stdfile = os.fdopen(saved_stdfile_fd, "wb", 0)

    # Open pseudo terminal reader as non-blocking.
    pty_master_file = os.fdopen(pty_master_fd, "rb", buffering=0)
    fl = fcntl.fcntl(pty_master_fd, fcntl.F_GETFL)
    fcntl.fcntl(pty_master_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    # Flush the C-level buffer before the output is redirected.
    flush_c(stdtype)

    # Redirect low level std[out|err] to slave_fd. This also reads std[out|err] of
    # sub-processes, c code, etc..
    stdfile.flush()
    os.dup2(pty_slave_fd, stdfile.fileno())

    return (
        original_stdfile_fd,
        pty_master_fd,
        pty_master_file,
        saved_stdfile_fd,
        saved_stdfile,
    )


def remove_ansi_str(line: str) -> str:
    ansi_escape = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", line)


def remove_ansi_bytes(line: bytes) -> bytes:
    ansi_escape = re.compile(rb"(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub(b"", line)


def _save_stream(
    stdout: Optional[_LowlevelRedirector],
    stderr: Optional[_LowlevelRedirector],
    queue,
) -> None:
    """
    In this thread we read the data from the pseudo-terminals in realtime (almost) and
    write it into the saved-stdout/saved-stderr files and into the return-files.

    The data that is written into the saved-stdout/saved-stderr files appears on the
    users terminal.

    The data that is written into the return-files will be returned with the CmdResult()
    object after the execution finished.
    """

    readable = {}

    if stdout:
        readable[stdout.master_fd] = stdout.saved_std_file

    if stderr:
        readable[stderr.master_fd] = stderr.saved_std_file

    should_break = 0
    data = None

    while True:
        if should_break > 0 and not data:
            if should_break < 3:
                should_break += 1
            else:
                break

        data = None

        for fd in select(readable, [], [], 0)[0]:
            data = os.read(fd, 4096)

            for line in data.splitlines(keepends=True):
                if stdout and fd == stdout.master_fd:
                    if not stdout.mute and stdout.saved_std_file:
                        stdout.saved_std_file.write(line)
                        stdout.saved_std_file.flush()

                    if not stdout.tty:
                        line = remove_ansi_bytes(line)

                    if stdout.text:
                        line = line.decode()
                        if isinstance(stdout.logfile, io.StringIO):
                            stdout.logfile.write(line)
                    else:
                        if isinstance(stdout.logfile, io.BytesIO):
                            stdout.logfile.write(line)

                elif stderr:
                    if not stderr.mute and stderr.saved_std_file:
                        stderr.saved_std_file.write(line)
                        stderr.saved_std_file.flush()

                    if not stderr.tty:
                        line = remove_ansi_bytes(line)

                    if stderr.text:
                        line = line.decode()
                        if isinstance(stderr.logfile, io.StringIO):
                            stderr.logfile.write(line)
                    else:
                        if isinstance(stderr.logfile, io.BytesIO):
                            stderr.logfile.write(line)

        try:
            queue.get(block=False)
            should_break = 1
        except Empty:
            pass

        time.sleep(0.001)


def _remove_lowlevel_redirector(
    stdtype: Std,
    saved_stdfile_fd: int,
    original_stdfile_fd: int,
) -> None:
    # # Flush the C-level buffer to redirected std[out|err].
    flush_c(stdtype)

    if stdtype == Std.OUT:
        sys.stdout.flush()
    else:
        sys.stderr.flush()

    # Set the stdfile output back to the original.
    os.dup2(saved_stdfile_fd, original_stdfile_fd)


class DuplexWriter:
    """
    This is a custom file writer, that writes to a StringIO and std[out|err] at the
    same time.
    """

    def __init__(
        self,
        stdtype: Optional[Std],
        logfile: Optional[Union[io.StringIO, io.BytesIO]],
        conf: Optional[Pipe],
    ):
        self.logfile_s: Optional[io.StringIO] = None
        self.logfile_b: Optional[io.BytesIO] = None

        if isinstance(logfile, io.TextIOBase):
            self.logfile_s = logfile
        elif isinstance(logfile, io.BytesIO):
            self.logfile_b = logfile

        self.conf: Optional[Pipe] = conf

        if stdtype == Std.OUT:
            self.stdfile: TextIO = sys.stdout
        else:
            self.stdfile: TextIO = sys.stderr

    def write(self, s):
        if self.conf and not self.conf.mute:
            self.stdfile.write(s)

        if self.conf and not self.conf.tty:
            s = remove_ansi_str(s)

        if self.conf and not self.conf.text:
            s = bytes(s, "utf-8")

            if self.logfile_b:
                self.logfile_b.write(s)
        else:
            if self.logfile_s:
                self.logfile_s.write(s)

    def flush(self) -> None:
        if not self.conf or not self.conf.mute:
            self.stdfile.flush()
        if self.logfile_s:
            self.logfile_s.flush()
        if self.logfile_b:
            self.logfile_b.flush()


def _close_redirector_files(redirector):
    """Close file descriptors if they exist."""
    if redirector:
        if getattr(redirector, "master_file", None):
            redirector.master_file.close()
        if getattr(redirector, "saved_std_file", None):
            redirector.saved_std_file.close()


@contextmanager
def redirect_stdfiles(
    stdout_conf=None,
    stdout_logfile=None,
    stderr_conf=None,
    stderr_logfile=None,
) -> Generator[None, None, None]:
    """"""
    stdout_low = None
    stderr_low = None
    stdout_high = None
    stderr_high = None
    queue = None
    pty_stream_writer = None

    if stdout_conf and stdout_conf.fd and (stdout_conf.save or stdout_conf.mute):
        stdout_low = _LowlevelRedirector(
            save=stdout_conf.save,
            text=stdout_conf.text,
            tty=stdout_conf.tty,
            mute=stdout_conf.mute,
            logfile=stdout_logfile,
        )
    elif stdout_conf and (stdout_conf.save or stdout_conf.mute):
        stdout_high = _HighlevelRedirector(stdout_logfile)

    if stderr_conf and stderr_conf.fd and (stderr_conf.save or stderr_conf.mute):
        stderr_low = _LowlevelRedirector(
            save=stderr_conf.save,
            text=stderr_conf.text,
            tty=stderr_conf.tty,
            mute=stderr_conf.mute,
            logfile=stderr_logfile,
        )
    elif stderr_conf and (stderr_conf.save or stderr_conf.mute):
        stderr_high = _HighlevelRedirector(stderr_logfile)

    try:
        if stdout_low:
            r = _setup_lowlevel_redirector(Std.OUT)
            stdout_low.original_std_fd = r[0]
            stdout_low.master_fd = r[1]
            stdout_low.master_file = r[2]
            stdout_low.saved_std_fd = r[3]
            stdout_low.saved_std_file = r[4]
        elif stdout_high:
            # sys.stdout = stdout_high.file
            sys.stdout = DuplexWriter(Std.OUT, stdout_high.file, stdout_conf)

        if stderr_low:
            r = _setup_lowlevel_redirector(Std.ERR)
            stderr_low.original_std_fd = r[0]
            stderr_low.master_fd = r[1]
            stderr_low.master_file = r[2]
            stderr_low.saved_std_fd = r[3]
            stderr_low.saved_std_file = r[4]
        elif stderr_high:
            # sys.stderr = stderr_high.file
            sys.stderr = DuplexWriter(Std.ERR, stderr_high.file, stderr_conf)

        if stdout_low or stderr_low:
            queue = Queue()

            pty_stream_writer = Thread(
                target=_save_stream,
                args=(stdout_low, stderr_low, queue),
                daemon=True,
            )
            pty_stream_writer.start()

        yield

    finally:
        if stdout_high:
            sys.stdout = sys.__stdout__

        if stderr_high:
            sys.stderr = sys.__stderr__

        if stdout_low or stderr_low:
            if stdout_low and stdout_low.saved_std_fd and stdout_low.original_std_fd:
                _remove_lowlevel_redirector(
                    Std.OUT, stdout_low.saved_std_fd, stdout_low.original_std_fd
                )

            if stderr_low and stderr_low.saved_std_fd and stderr_low.original_std_fd:
                _remove_lowlevel_redirector(
                    Std.ERR, stderr_low.saved_std_fd, stderr_low.original_std_fd
                )

            if queue:
                queue.put(1)  # Send stop signal.

            if pty_stream_writer:
                pty_stream_writer.join()

            _close_redirector_files(stdout_low)
            _close_redirector_files(stderr_low)


@contextmanager
def no_redirector() -> Generator[None, None, None]:
    yield
