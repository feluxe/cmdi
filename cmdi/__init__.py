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
[] TODO: Add test for variations of CustomCmdResult.
[] TODO: Add tests for _set_color().
"""

from typing import NamedTuple, Union, TextIO, Optional, Iterable, List, Callable, Any
from contextlib import redirect_stdout, redirect_stderr
from functools import partial, wraps
import io
import sys
from sty import fg


class Status:
    """
    Can be used to set 'status' value CustomCmdResult.
    """
    ok = 'Ok'
    error = 'Error'
    warning = 'Warning'
    skip = 'Skip'


class StatusColor:
    """
    Can be used to set 'color' value in CustomCmdResult.
    """
    green = 0
    red = 1
    yellow = 2


class StdOutIO(io.StringIO):
    """
    This is a custom file writer, that writes to a StringIO and StdOut
    at the same time.
    """

    def write(self, s):
        super().write(s)
        sys.stdout.write(s)


class StdErrIO(io.StringIO):
    """
    This is a custom file writer, that writes to a StringIO and StdErr
    at the same time.
    """

    def write(self, s):
        super().write(s)
        sys.stderr.write(s)


class CmdResult(NamedTuple):
    """
    The default result type.
    Each function that is decorated with @command returns this type.
    """
    val: Optional[Any]
    code: Optional[int]
    name: Optional[str]
    status: Optional[str]
    color: Optional[int]
    out: Optional[TextIO]
    err: Optional[TextIO]


def strip_args(loc):

    if 'cmdargs' in loc:
        del loc['cmdargs']
    return loc


def set_result(
    val: Optional[Any] = None,
    code: Optional[int] = None,
    status: Optional[str] = None,
    color: Optional[int] = None,
) -> CmdResult:
    """"""

    return CmdResult(
        val=val,
        code=code,
        name=None,
        status=status,
        color=color,
        out=None,
        err=None
    )


def print_title(
    string: str,
    color: bool = True,
    stdout: TextIO = sys.stdout,
):
    """
    Just a convenient way to print the title with color and all.
    """

    sep = '\n' + (len(string) + 5) * '-'

    if color:
        string = f'\n{fg.cyan}Cmd: {string}{sep}{fg.rs}'
    else:
        string = f'\nCmd: {string}{sep}'

    print(string, file=stdout)


def print_status(
    result: CmdResult,
    color: bool = True,
) -> None:
    """
    Just a convenient way to print the status with color and all.
    """

    if not isinstance(result, CmdResult):
        raise TypeError(
            'Error: param "result" must be of type: "CmdResult" but it is of type: '
            + type(result)
        )

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


def print_summary(
    results: Union[Optional[CmdResult], List[Optional[CmdResult]]],
    color=True,
    headline=True,
) -> None:
    """
    Just a convenient way to print the summary of one or multiple commands with
    color and all.
    """
    if headline:
        if color:
            print(fg.cyan + '\nSummary\n' + 7 * '-' + fg.rs)
        else:
            print('Summary:' + 8 * '-')

    if not results:
        return

    elif isinstance(results, CmdResult):
        print_status(results, color)

    elif isinstance(results, Iterable):
        for item in results:
            print_summary(item, color, headline=False)


def _set_color(
    color: Optional[int],
    status: Optional[str],
) -> int:
    """
    Automatically determine color value.
    """
    if color:
        return color

    if status in [Status.ok, Status.skip]:
        return StatusColor.green
    elif status == Status.error:
        return StatusColor.red
    elif Status.warning:
        return StatusColor.yellow
    else:
        return StatusColor.yellow


def command(decorated_func):
    """
    The @command decorator that turns a function into a command.
    """

    @wraps(decorated_func)
    def command_wrapper(*args, **kwargs) -> CmdResult:
        """"""
        # Set default parameters.
        catch_err = kwargs.get('_catch_err', True)
        verbose = kwargs.get('_verbose', True)
        colorful = kwargs.get('_color', True)
        out = kwargs.get('_out') or sys.stdout
        err = kwargs.get('_err') or sys.stderr
        name = decorated_func.__name__

        # Redirect stdout/stderr to files given by user.
        with redirect_stdout(out):
            with redirect_stderr(err):
                """"""
                if verbose:
                    print_title(name, color=colorful, stdout=out)

                try:
                    return_val = decorated_func(*args, **kwargs)

                    # If the user returns a CustomCmdResult, we take it and
                    # apply default values if necessary.
                    if isinstance(return_val, CmdResult):

                        val = return_val.val
                        code = return_val.code or 0
                        status = return_val.status or Status.ok
                        color = _set_color(
                            color=return_val.color, status=status
                        )
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
                            val=return_val,
                            code=0,
                            name=name,
                            status=Status.ok,
                            color=StatusColor.green,
                            out=kwargs.get('_out'),
                            err=kwargs.get('_err'),
                        )

                # If a function call fails, we wrap the error data in a
                # CmdResult and return that.
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
