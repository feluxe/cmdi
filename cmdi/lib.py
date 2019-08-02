"""
A decorator (`@command`) that applies a special interface called the _Command Interface_
to its decorated function. Initially written for the _buildlib_.

The _Command Interface_ allows you to control the exectuion of a function:

-   It allows you to save/direct output streams (stdout/stderr) for its decorated function.
-   It allows you to catch exceptions for its decorated function and return them with
    the `CmdResult()`, including _return codes_, _error messages_ and colored _status messages_.
-   It allows you to print statuses and summaries for the command results.

A function that is decorated with `@command` can receive a set of sepcial keyword
arguments (`_verbose=`, `_stdout=`, `_stderr=`, ...) and it always returns a `CmdResult()` object.

"""
import os
import fcntl
import subprocess as sp
from threading import Thread
from queue import Queue, Empty
from copy import deepcopy
import time
from contextlib import redirect_stdout, redirect_stderr, contextmanager
import io
import sys
from dataclasses import dataclass
import ctypes
import pty
import re
import termios

from typing import NamedTuple, Union, TextIO, Optional, Iterable, List, Callable, Any, Dict, IO, Iterator, Tuple


# String Styling.
fg_cyan = '\x1b[36m'
fg_green = '\x1b[32m'
fg_yellow = '\x1b[33m'
fg_red = '\x1b[31m'
fg_rs = '\x1b[39m'


class Status:
    """
    Can be used to set 'status' value for CmdResult.
    """
    ok = 'Ok'
    error = 'Error'
    warning = 'Warning'
    skip = 'Skip'


class StatusColor:
    """
    Can be used to set 'color' value for CmdResult.
    """
    green = 0
    red = 1
    yellow = 2


@dataclass
class CmdResult:
    """
    The Command Result Type.
    Each function that is decorated with @command returns this type.
    """
    val: Optional[Any] = None
    code: Optional[int] = None
    name: Optional[str] = None
    status: Optional[str] = None
    color: Optional[int] = None
    stdout: Optional[Union[str, bytes]] = None
    stderr: Optional[Union[str, bytes]] = None


def strip_cmdargs(locals_: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove cmdargs from locals.

    Example usage:

      def foo(x):
          return x * 2

      @command
      def foo_cmd(x, **cmdargs):
          return foo(strip_cmdargs(locals()))

    """
    keys = [
        'kwargs', 'cmdargs', '_verbose', '_stdout', '_stderr', '_catch_err', '_color'
    ]

    for key in keys:
        if key in locals_:
            if key == 'kwargs' and isinstance(key, dict):
                for sub_k in key:
                    if sub_k in keys:
                        del key[sub_k]
            else:
                del locals_[key]
    return locals_


def _print_title(
    name: str,
    color: bool = True,
    file: IO[str] = None,
) -> None:
    sep = '\n' + (len(name) + 5) * '-'

    if color:
        name = f'\n{fg_cyan}Cmd: {name}{sep}{fg_rs}'
    else:
        name = f'\nCmd: {name}{sep}'

    print(name, file=file or sys.stdout)


def print_title(
    result: CmdResult,
    color: bool = True,
    file: Optional[IO[str]] = None,
) -> None:
    """
    Print command title template.

    Example output:

      Cmd: my_cmd
      -----------

    """
    _print_title(result.name or "", color=color, file=file or sys.stdout)


def print_status(
    result: CmdResult,
    color: bool = True,
    file: Optional[IO[str]] = None,
) -> None:
    """
    Print the status of a command result.

    Example output:

      my_cmd: Ok

    """
    if not isinstance(result, CmdResult):
        raise TypeError(
            f'Error: param "result" must be of type: "CmdResult" but it is of type: {type(result)}'
        )

    r = result
    f = file or sys.stdout

    if color:
        if r.color == StatusColor.green:
            print(f'{fg_green}{r.name}: {r.status}{fg_rs}', file=f)
        elif r.color == StatusColor.yellow:
            print(f'{fg_yellow}{r.name}: {r.status}{fg_rs}', file=f)
        else:
            print(f'{fg_red}{r.name}: {r.status}{fg_rs}', file=f)

    else:
        print(f'{r.name}: {r.status}', file=f)


def print_result(
    result: CmdResult,
    color: bool = True,
    file: Optional[IO[str]] = None,
) -> None:
    """
    Print out the CmdResult object.

    Example output:

      Cmd: my_cmd
      -----------
      Stdout:
      Runtime output of my_cmd...
      Stderr:
      Some err
      foo_cmd3: Ok

    """
    colo = fg_cyan if color else ""
    rs = fg_rs if color else ""
    f = file or sys.stdout

    print_title(result)

    # Handle Stdout
    if result.stdout:
        print(f"{colo}Stdout:{rs}\n", file=f)
    if isinstance(result.stdout, io.StringIO):
        print(result.stdout.getvalue() or "", file=f)
    elif isinstance(result.stdout, str):
        print(result.stdout or "", file=f)

    # Handle Stderr
    if result.stderr:
        print(f"{colo}Stderr:{rs}\n", file=f)
    if isinstance(result.stderr, io.StringIO):
        print(result.stderr.getvalue() or "", file=f)
    elif isinstance(result.stderr, str):
        print(result.stdout or "", file=f)

    print_status(result)


def print_summary(
    results: Union[Optional[CmdResult], List[Optional[CmdResult]]],
    color: bool = True,
    headline: bool = True,
    file: Optional[IO[str]] = None,
) -> None:
    """
    Print the summary of one or multiple commands.

    Example outpup:

      Summary
      -------
      foo_cmd1: Ok
      foo_cmd2: Ok
      foo_cmd3: Error

    """
    f = file or sys.stdout

    if headline:
        if color:
            print(fg_cyan + '\nSummary\n' + 7 * '-' + fg_rs, file=f)
        else:
            print('\nSummary\n' + 7 * '-', file=f)

    if isinstance(results, CmdResult):
        print_status(results, color=color, file=f)

    elif isinstance(results, Iterable):
        for item in results:
            print_summary(item, color=color, headline=False, file=f)

    else:
        return


def _set_status(status: Optional[str], code: Optional[int]) -> str:
    """
    Automatically determine status value.
    """
    if status is not None:
        return status
    elif code == 0:
        return Status.ok
    else:
        return Status.error


def _set_color(status: Optional[str], color: Optional[int]) -> int:
    """
    Automatically determine color value.
    """
    if color:
        return color
    elif status in [Status.ok, Status.skip]:
        return StatusColor.green
    elif status == Status.warning:
        return StatusColor.yellow
    else:
        return StatusColor.red



POPEN_DEFAULTS: Dict[str, Any] = {
    "stdout": sp.PIPE,
    "stderr": sp.PIPE,
    "bufsize": 1,
    "text": True,
}


def _enqueue_output(file: IO[str], queue: Queue) -> None:
    for line in iter(file.readline, ''):
        queue.put(line)
    file.close()


def read_popen_pipes(
    p: sp.Popen,
    interval: int = 0,
) -> Iterator[Tuple[str, str]]:

    with ThreadPoolExecutor(2) as pool:
        q_stdout: Queue = Queue()
        q_stderr: Queue = Queue()

        pool.submit(_enqueue_output, p.stdout, q_stdout)
        pool.submit(_enqueue_output, p.stderr, q_stderr)

        while True:

            if p.poll() is not None and q_stdout.empty() and q_stderr.empty():
                break

            out_line = err_line = ''

            try:
                out_line = q_stdout.get_nowait()
                err_line = q_stderr.get_nowait()
            except Empty:
                pass

            yield (out_line, err_line)

            time.sleep(interval / 1000)


def resolve_popen(
    p: sp.Popen,
    save_stdout: bool = False,
    save_stderr: bool = False,
    mute_stdout: bool = False,
    mute_stderr: bool = False,
    catch: List[int] = [],
    interval: int = 0,
) -> sp.CompletedProcess:

    args = p.args
    from typing import cast

    stdout = cast(str, "" if save_stdout else None)
    stderr = cast(str, "" if save_stderr else None)

    for out_line, err_line in read_popen_pipes(p, interval):

        if not mute_stdout:
            sys.stdout.write(out_line)
        if not mute_stderr:
            sys.stderr.write(err_line)
        if save_stdout:
            stdout += out_line
        if save_stderr:
            stderr += err_line

    code = p.poll()

    if code != 0 and code not in catch and '*' not in catch:
        raise sp.CalledProcessError(code, args, stdout, stderr)

    return sp.CompletedProcess(args, code, stdout, stderr)


def run_subprocess(
    args: List[str],
    save_stdout: bool = False,
    save_stderr: bool = False,
    mute_stdout: bool = False,
    mute_stderr: bool = False,
    catch: List[int] = [],
    interval: int = 0,
    cwd: Optional[str] = None,
    shell: bool = False,
):
    p = sp.Popen(args, shell=shell, cwd=cwd, **POPEN_DEFAULTS)

    return resolve_popen(
        p,
        save_stdout=save_stdout,
        save_stderr=save_stderr,
        mute_stdout=mute_stdout,
        mute_stderr=mute_stderr,
        catch=catch,
        interval=interval,
    )
