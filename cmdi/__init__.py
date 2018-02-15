"""
[x] should print title.
[x] should print result.status
[x] should allow coloring for printing title and summary.
[x] should allow use of custom stdout files
[x] should allow use of custom stderr files
[x] should return value
[x] should return custom stdout file
[x] should return custom stderr file
[x] should return returncode
[x] should return status
[] should leverage asyncio
"""

from typing import NamedTuple, Union, TextIO, Tuple
from contextlib import redirect_stdout, redirect_stderr
import io
import sys
from sty import fg


class Status:
    ok = 'Ok'
    error = 'Error'


class StatusColor:
    green = 0
    red = 1
    yellow = 2


class StdOutIO(io.StringIO):

    def write(self, s):
        super().write(s)
        sys.stdout.write(s)


class StdErrIO(io.StringIO):

    def write(self, s):
        super().write(s)
        sys.stderr.write(s)


class CmdResult(NamedTuple):
    val: any
    code: int
    name: str
    status: str
    color: int
    out: TextIO
    err: TextIO


def print_title(
    string: str,
    color: bool = True,
    stdout: TextIO = sys.stdout,
):
    if color:
        string = f'\n{fg.cyan}Run: {string}{fg.rs}\n'
    else:
        string = f'\nRun: {string}\n'
    print(string, file=stdout)


def print_status(
    result: CmdResult,
    color: bool = True,
):
    if not isinstance(result, CmdResult):
        raise TypeError('Error: param "result" must be of type: "CmdResult".')

    r = result

    if color:
        if r.code == 0 and r.color == StatusColor.green:
            print(f'{fg.green}{r.name}: {r.status}{fg.rs}', file=r.out)
        elif r.code == 0 and r.color == StatusColor.yellow:
            print(f'{fg.yellow}{r.name}: {r.status}{fg.rs}', file=r.out)
        else:
            print(f'{fg.red}{r.name}: {r.status}{fg.rs}', file=r.err)
    else:
        if r.code == 0:
            print(f'{r.name}: {r.status}', file=r.out)
        else:
            print(f'{r.name}: {r.status}', file=r.err)


def command(decorated_func):
    """"""

    def command_wrapper(*args, **kwargs) -> CmdResult:
        """"""
        catch_err = kwargs.get('_catch_err', True)
        colorful = kwargs.get('_color', True)
        out = kwargs.get('_out') or sys.stdout
        err = kwargs.get('_err') or sys.stderr
        name = decorated_func.__name__

        with redirect_stdout(out):
            with redirect_stderr(err):
                """"""
                print_title(
                    name,
                    color=colorful,
                    stdout=out
                )

                try:
                    return_val = decorated_func(*args, **kwargs)

                    if isinstance(return_val, CmdResult):
                        result = return_val
                    else:
                        result = CmdResult(
                            val=return_val,
                            code=0,
                            name=name,
                            status=Status.ok,
                            color=StatusColor.green,
                            out=out,
                            err=err,
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
                        out=out,
                        err=err,
                    )

                print_status(
                    result,
                    color=colorful,
                )

                return result

    return command_wrapper
