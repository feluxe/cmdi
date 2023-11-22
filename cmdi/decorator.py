import io
import subprocess as sp
import sys
from copy import deepcopy
from dataclasses import dataclass
from functools import wraps
from typing import IO, Any, Callable, Optional, TypeVar

from .lib import (
    CmdResult,
    Status,
    StatusColor,
    _print_title,
    _set_color,
    _set_status,
    print_status,
)
from .redirector import _STD, no_redirector, redirect_stdfiles

STDOUT = _STD.OUT


@dataclass
class Pipe:
    save: bool = True
    text: bool = True
    dup: bool = False
    tty: bool = False
    mute: bool = False


def _get_logfile(stdtype, args) -> Optional[IO]:

    if not args:
        return None

    if not args.save:
        return None

    if args.text:
        return io.StringIO()
    else:
        return io.BytesIO()


def _get_redirector(stdout_pipe, stdout_logfile, stderr_pipe, stderr_logfile):

    if not stdout_pipe and not stderr_pipe:
        return no_redirector()
    else:
        return redirect_stdfiles(
            stdout_pipe, stdout_logfile, stderr_pipe, stderr_logfile
        )


Func = TypeVar("Func", bound=Callable[..., Any])


def command(decorated_func: Func) -> Callable[..., CmdResult]:
    """
    The @command decorator that turns a function into a command.
    """

    @wraps(decorated_func)
    def command_wrapper(*args, **kwargs) -> CmdResult:

        # Set default parameters.
        name = decorated_func.__name__
        catch_err = kwargs.get("_catch_err", True)
        verbose = kwargs.get("_verbose", True)
        colorful = kwargs.get("_color", True)
        stdout_pipe = kwargs.get("_stdout")
        stderr_pipe = kwargs.get("_stderr")

        if verbose:
            _print_title(name, color=colorful)

        stdout_logfile = _get_logfile(_STD.OUT, stdout_pipe)
        if stderr_pipe == _STD.OUT:
            stderr_logfile = stdout_logfile
            stderr_pipe = deepcopy(stdout_pipe)
        else:
            stderr_logfile = _get_logfile(_STD.ERR, stderr_pipe)

        with _get_redirector(stdout_pipe, stdout_logfile, stderr_pipe, stderr_logfile):

            try:

                cleaned_kwargs = {
                    k: v
                    for k, v in kwargs.items()
                    if k
                    not in ["_stdout", "_stderr", "_catch_err", "_verbose", "_color"]
                }

                item = decorated_func(*args, **cleaned_kwargs)
                # item = decorated_func(*args, **kwargs)

                # If the user returns a CustomCmdResult, we take it and
                # apply default values if necessary.
                if isinstance(item, CmdResult):

                    val = item.val
                    code = item.code or 0
                    status = _set_status(item.status, code)
                    color = _set_color(status, item.color)

                    result = CmdResult(
                        val=val,
                        code=code,
                        status=status,
                        color=color,
                        name=name,
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
                    )

            except sp.CalledProcessError as e:

                if e.stderr:
                    print(e.stderr, file=sys.stderr)

                if not catch_err:
                    raise e

                result = CmdResult(
                    val=None,
                    code=e.returncode,
                    name=name,
                    status=Status.error,
                    color=StatusColor.red,
                )

            except Exception as e:  # pylint: disable=broad-except

                print(e, file=sys.stderr)

                if not catch_err:
                    sys.exit(1)

                result = CmdResult(
                    val=None,
                    code=1,
                    name=name,
                    status=Status.error,
                    color=StatusColor.red,
                )

        if isinstance(stdout_logfile, (io.StringIO, io.BytesIO)):
            result.stdout = stdout_logfile.getvalue()
        if isinstance(stderr_logfile, (io.StringIO, io.BytesIO)):
            if not kwargs.get("_stderr") == _STD.OUT:
                result.stderr = stderr_logfile.getvalue()

        if verbose:
            print_status(
                result,
                color=colorful,
            )

        return result

    return command_wrapper
