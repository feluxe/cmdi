"""
A decorator (`@command`) that applies a special interface called the _Command Interface_
to its decorated function. Initially written for the _buildlib_.

The _Command Interface_ allows you to control the exectuion of a function:

-   It allows you to save/redirect output streams (stdout/stderr) for its decorated function.
-   It allows you to catch exceptions for its decorated function and return them with
    the `CmdResult()`, including _return codes_, _error messages_ and colored _status messages_.
-   It allows you to print statuses and summaries for the command results.

A function that is decorated with `@command` can receive a set of sepcial keyword
arguments (`_verbose=`, `_stdout=`, `_stderr=`, ...) and it always returns a `CmdResult()` object.

"""

import io
import subprocess as sp
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from queue import Empty, Queue
from typing import (
    IO,
    Any,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Literal,
    NoReturn,
    Optional,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
)

from typing_extensions import NotRequired


class Std(Enum):
    OUT = "stdout"
    ERR = "stderr"


STDOUT = Std.OUT

# Internal string styling.
fg_cyan = "\x1b[36m"
fg_green = "\x1b[32m"
fg_yellow = "\x1b[33m"
fg_red = "\x1b[31m"
fg_rs = "\x1b[39m"


@dataclass
class Pipe:
    """
    Configuration flags for controlling stream redirection behavior.

    Attributes:
        save (bool): If True, save (buffer/record) the output to a log or memory.
        text (bool): If True, decode bytes to text (str); if False, keep as bytes.
        tty (bool): If True, treat the output stream as a TTY/terminal (keep ANSI codes).
            If False, strip ANSI escape sequences.
        mute (bool): If True, suppress output from appearing in the user's terminal.
        fd (bool): If True, perform low-level file descriptor duplication/redirection
            (e.g., using os.dup/os.dup2 with PTY support). Needed to capture output
            from subprocesses and C extensions.
    """

    save: bool = True
    text: bool = True
    tty: bool = False
    mute: bool = False
    fd: bool = False


class CmdArgs(TypedDict, total=False):
    """
    Configuration flags for handling a command.

    Attributes:
        _raise (bool): If True, runtine exceptions are raised.
        _verbose (bool): If True, status messages (like command title, results, etc.) will be printed.
        _color (bool): If True, status messages will use colors.
        _stdout (Pipe, None): Handle the command out. Allows muting, redirecting, saving of stdout/stderr (and more).
        _stderr (Pipe, Std.Out, None): See _stdout. Use Std.Out or STDOUT to redirect stderr to stdout.
    """

    _raise: NotRequired[bool]
    _verbose: NotRequired[bool]
    _color: NotRequired[bool]
    _stdout: NotRequired[Union[Pipe, None]]
    _stderr: NotRequired[Union[Pipe, Literal[Std.OUT], None]]


class Status(Enum):
    """
    Can be used to set 'status' value for CmdResult.
    """

    ok = 0
    error = 1
    warning = 2
    skip = 3

    def __str__(self):
        return str(self.name.capitalize())


class StatusColor(Enum):
    """
    Can be used to set 'color' value for CmdResult.
    """

    green = 0
    red = 1
    yellow = 2

    def __str__(self):
        return str(self.name.capitalize())


def _set_status(status: Optional[Status], code: Optional[int]) -> Status:
    """
    Determine Status from given 'status' or given 'return code'.
    """
    try:
        return Status(status)
    except ValueError:
        is_int = isinstance(code, int)
        if is_int and code == 0:
            return Status.ok
        elif is_int:
            return Status.error
        else:
            raise ValueError("Unknown return status.")


def _set_color(color: Optional[StatusColor], status: Optional[Status]) -> StatusColor:
    """
    Determine StatusColor from given 'color' or given 'status'.
    """
    try:
        return StatusColor(color)
    except ValueError:
        if status in [Status.ok, Status.skip]:
            return StatusColor.green
        elif status == Status.warning:
            return StatusColor.yellow
        elif status == Status.error:
            return StatusColor.red
        else:
            raise ValueError("Unknown status color.")


T = TypeVar("T")


class CmdResult(Generic[T]):
    """
    The Command Result Type.
    Each function that is decorated with @command returns this type.
    """

    def __init__(
        self,
        value: T,
        code: int,
        name: str = "cmdi.command",
        status: Optional[Status] = None,
        color: Optional[StatusColor] = None,
        stdout: str = "",
        stderr: str = "",
        stdout_b: bytes = b"",
        stderr_b: bytes = b"",
    ):
        status = _set_status(status, code)
        color = _set_color(color, status)

        self.value: T = value
        self.code: int = code
        self.name: Optional[str] = name
        self.status: Status = status
        self.color: StatusColor = color
        self.stdout: str = stdout
        self.stderr: str = stderr
        self.stdout_b: bytes = stdout_b
        self.stderr_b: bytes = stderr_b


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
    reserved_keys = [
        "kwargs",
        "cmdargs",
        "_verbose",
        "_stdout",
        "_stderr",
        "_raise",
        "_color",
    ]

    for key in reserved_keys:
        if key in locals_:
            if key == "kwargs" and isinstance(locals_[key], dict):
                sub_dict = locals_[key]
                for sub_k in sub_dict:
                    if sub_k in reserved_keys:
                        del sub_dict[sub_k]
            else:
                del locals_[key]

    return locals_


def _print_title(
    name: str,
    color: bool = True,
    file: Optional[IO[str]] = None,
) -> None:
    sep = "\n" + (len(name) + 5) * "-"

    if color:
        name = f"\n{fg_cyan}Cmd: {name}{sep}{fg_rs}"
    else:
        name = f"\nCmd: {name}{sep}"

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
    r = result
    f = file or sys.stdout

    if color:
        if r.color == StatusColor.green:
            print(f"{fg_green}{r.name}: {r.status}{fg_rs}", file=f)
        elif r.color == StatusColor.yellow:
            print(f"{fg_yellow}{r.name}: {r.status}{fg_rs}", file=f)
        else:
            print(f"{fg_red}{r.name}: {r.status}{fg_rs}", file=f)

    else:
        print(f"{r.name}: {r.status}", file=f)


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
            print(fg_cyan + "\nSummary\n" + 7 * "-" + fg_rs, file=f)
        else:
            print("\nSummary\n" + 7 * "-", file=f)

    if isinstance(results, CmdResult):
        print_status(results, color=color, file=f)

    elif isinstance(results, Iterable):
        for item in results:
            print_summary(item, color=color, headline=False, file=f)

    else:
        return


def exit_with(
    result: Union[CmdResult, str], code_overwrite: Optional[int] = None
) -> NoReturn:
    """Print stdout/stderr and exit with 'code'"""

    if isinstance(result, CmdResult):
        if result.stdout:
            print(result.stdout)
        if result.stdout_b:
            print(result.stdout_b.decode())
        if result.stderr:
            sys.stderr.write(f"{result.stderr}\n")
        if result.stderr_b:
            sys.stderr.write(f"{result.stderr_b.decode()}\n")
        code = code_overwrite if code_overwrite is not None else result.code
        sys.exit(code)

    if code_overwrite == 0 or code_overwrite is None:
        print(result)
    else:
        sys.stderr.write(result + "\n")
    sys.exit(code_overwrite)


def _enqueue_output(file: IO[str], queue: Queue) -> None:
    for line in iter(file.readline, ""):
        queue.put(line)
    file.close()


def read_popen_pipes(
    p: sp.Popen,
    interval: int = 0,
) -> Iterator[Tuple[str, str]]:
    """
    Read the ouput of 'Popen' for both stdout and stderr in real time line by line.
    This returns an Iterator which gives you a tuple like this:
        (out_str, err_str)
    """
    # Determine how many threads we need based on available streams
    threads_needed = sum([p.stdout is not None, p.stderr is not None])

    # If no streams are available, just wait for process to complete
    if threads_needed == 0:
        while p.poll() is None:
            yield ("", "")
            time.sleep(interval / 1000)
        return

    with ThreadPoolExecutor(threads_needed) as pool:
        q_stdout: Optional[Queue] = Queue() if p.stdout else None
        q_stderr: Optional[Queue] = Queue() if p.stderr else None

        if p.stdout and q_stdout is not None:
            pool.submit(_enqueue_output, p.stdout, q_stdout)
        if p.stderr and q_stderr is not None:
            pool.submit(_enqueue_output, p.stderr, q_stderr)

        while True:
            # Check if process is done and all queues are empty
            if p.poll() is not None:
                stdout_empty = q_stdout.empty() if q_stdout else True
                stderr_empty = q_stderr.empty() if q_stderr else True
                if stdout_empty and stderr_empty:
                    break

            out_line = err_line = ""
            try:
                if q_stdout:
                    out_line = q_stdout.get_nowait()
            except Empty:
                pass

            try:
                if q_stderr:
                    err_line = q_stderr.get_nowait()
            except Empty:
                pass

            yield (out_line, err_line)
            time.sleep(interval / 1000)
