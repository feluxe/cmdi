"""
A decorator (`@command`) that applies a special interface called the _Command Interface_
to its decorated function. Initially written for the _buildlib_.

The _Command Interface_ allows you to control the exectuion of a function:

-   It allows you to save/direct output streams (stdout/stderr) for its decorated function.
-   It allows you to catch exceptions for its decorated function and return them with
    the `CmdResult()`, including _return codes_, _error messages_ and colored _status messages_.
-   It allows you to print statuses and summaries for the command results.

A function that is decorated with `@command` can receive a set of sepcial keyword
arguments (`_verbose=`, `_out=`, `_err=`, ...) and it always returns a `CmdResult()` object.

"""
import subprocess as sp
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
import time
from contextlib import redirect_stdout, redirect_stderr
from functools import partial, wraps
import io
import sys
from sty import fg
from dataclasses import dataclass

from typing import NamedTuple, Union, TextIO, Optional, Iterable, List, Callable, Any, Dict, IO, Iterator, Tuple


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


class StdOutIO(io.StringIO):
    """
    This is a custom file writer, that writes to a StringIO and StdOut
    at the same time.

    Example usage:

      from cmdi import StdOutIO

      result = my_cmd(_out=StdOutIO)
      print(result.out.getvalue())

    """

    def write(self, s):
        super().write(s)
        sys.stdout.write(s)


class StdErrIO(io.StringIO):
    """
    This is a custom file writer, that writes to a StringIO and StdErr
    at the same time.

    Example usage:

      from cmdi import StdErrIO

      result = my_cmd(_err=StdErrIO)
      print(result.err.getvalue())

    """

    def write(self, s):
        super().write(s)
        sys.stderr.write(s)


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
    out: Optional[TextIO] = None
    err: Optional[TextIO] = None


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
    if 'cmdargs' in locals_:
        del locals_['cmdargs']
    return locals_


def _print_title(
    name: str,
    color: bool = True,
    file: IO[str] = None,
) -> None:
    sep = '\n' + (len(name) + 5) * '-'

    if color:
        name = f'\n{fg.cyan}Cmd: {name}{sep}{fg.rs}'
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
            print(f'{fg.green}{r.name}: {r.status}{fg.rs}', file=f)
        elif r.color == StatusColor.yellow:
            print(f'{fg.yellow}{r.name}: {r.status}{fg.rs}', file=f)
        else:
            print(f'{fg.red}{r.name}: {r.status}{fg.rs}', file=f)

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
    colo = fg.cyan if color else ""
    rs = fg.rs if color else ""
    f = file or sys.stdout

    print_title(result)

    # Handle Stdout
    if result.out:
        print(f"{colo}Stdout:{rs}\n", file=f)
    if isinstance(result.out, io.StringIO):
        print(result.out.getvalue() or "", file=f)
    elif isinstance(result.out, str):
        print(result.out or "", file=f)

    # Handle Stderr
    if result.err:
        print(f"{colo}Stderr:{rs}\n", file=f)
    if isinstance(result.err, io.StringIO):
        print(result.err.getvalue() or "", file=f)
    elif isinstance(result.err, str):
        print(result.out or "", file=f)

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
            print(fg.cyan + '\nSummary\n' + 7 * '-' + fg.rs, file=f)
        else:
            print('Summary:' + 8 * '-', file=f)

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


def command(decorated_func: Callable):
    """
    The @command decorator that turns a function into a command.
    """

    @wraps(decorated_func)
    def command_wrapper(*args, **kwargs) -> CmdResult:
        """"""
        # Set default parameters.
        name = decorated_func.__name__
        catch_err = kwargs.get('_catch_err', True)
        verbose = kwargs.get('_verbose', True)
        colorful = kwargs.get('_color', True)
        out = kwargs.get('_out') or sys.stdout
        err = kwargs.get('_err') or sys.stderr

        if verbose:
            _print_title(name, color=colorful)

        # Redirect stdout/stderr to files given by user.
        with redirect_stdout(out):

            with redirect_stderr(err):

                try:
                    item = decorated_func(*args, **kwargs)

                    # If the user returns a CustomCmdResult, we take it and
                    # apply default values if necessary.
                    if isinstance(item, CmdResult):

                        val = item.val
                        code = item.code or 0
                        status = _set_status(item.status, code)
                        color = _set_color(status, item.color)
                        out = kwargs.get('_out')
                        err = kwargs.get('_err')

                        result = CmdResult(
                            val=val,
                            code=code,
                            status=status,
                            color=color,
                            name=name,
                            out=kwargs.get('_out'),
                            err=kwargs.get('_err'),
                        )

                    # If the return type is none of CmdResult/CustomCmdResult,
                    # we wrap the default CmdResult around the return value.
                    else:
                        result = CmdResult(
                            val=item,
                            code=0,
                            name=name,
                            status=Status.ok,
                            color=StatusColor.green,
                            out=kwargs.get('_out'),
                            err=kwargs.get('_err'),
                        )

                except sp.CalledProcessError as e:

                    print(e, file=err)

                    if not catch_err:
                        sys.exit(1)

                    result = CmdResult(
                        val=None,
                        code=e.returncode,
                        name=name,
                        status=Status.error,
                        color=StatusColor.red,
                        out=kwargs.get('_out'),
                        err=kwargs.get('_err'),
                    )

                except Exception as e:

                    print(e, file=err)

                    if not catch_err:
                        sys.exit(1)

                    result = CmdResult(
                        val=None,
                        code=1,
                        name=name,
                        status=Status.error,
                        color=StatusColor.red,
                        out=kwargs.get('_out'),
                        err=kwargs.get('_err'),
                    )

        if verbose:
            print_status(
                result,
                color=colorful,
            )

        return result

    return command_wrapper


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
    interval: int = 10,
) -> Iterator[Tuple[str, str]]:

    with ThreadPoolExecutor(2) as pool:
        q_stdout: Queue = Queue()
        q_stderr: Queue = Queue()

        pool.submit(_enqueue_output, p.stdout, q_stdout)
        pool.submit(_enqueue_output, p.stderr, q_stderr)

        loop_should_run = True

        while loop_should_run:

            if p.poll() is not None:
                loop_should_run = False

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
    interval: int = 10,
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
    interval: int = 10,
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
