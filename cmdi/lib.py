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
from enum import Enum

from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue
from typing import (
    IO,
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
    TypeVar,
    Generic,
)

# String Styling.
fg_cyan = "\x1b[36m"
fg_green = "\x1b[32m"
fg_yellow = "\x1b[33m"
fg_red = "\x1b[31m"
fg_rs = "\x1b[39m"


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
            raise ValueError(f"Unknown return status.")


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
        val: T,
        code: int,
        name: str,
        status: Optional[Status],
        color: Optional[StatusColor],
        stdout: Optional[Union[str, bytes]] = None,
        stderr: Optional[Union[str, bytes]] = None,
    ):
        status = _set_status(status, code)
        color = _set_color(color, status)

        self.val: T = val
        self.code: int = code
        self.name: str = name
        self.status: Status = status
        self.color: StatusColor = color
        self.stdout: Optional[Union[str, bytes]] = stdout
        self.stderr: Optional[Union[str, bytes]] = stderr


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
        "_catch_err",
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
    if not isinstance(result, CmdResult):
        raise TypeError(
            f'Error: param "result" must be of type: "CmdResult" but it is of type: {type(result)}'
        )

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

    elif isinstance(
        results, Iterable
    ):  # pylint: disable=isinstance-second-argument-not-valid-type
        for item in results:
            print_summary(item, color=color, headline=False, file=f)

    else:
        return


def _enqueue_output(file: IO[str], queue: Queue) -> None:
    for line in iter(file.readline, ""):
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

            out_line = err_line = ""

            try:
                out_line = q_stdout.get_nowait()
                err_line = q_stderr.get_nowait()
            except Empty:
                pass

            yield (out_line, err_line)

            time.sleep(interval / 1000)
