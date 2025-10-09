import io
import subprocess as sp
import sys
from contextlib import _GeneratorContextManager
from copy import deepcopy
from functools import wraps
from typing import (
    IO,
    Callable,
    Literal,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from typing_extensions import ParamSpec

from cmdi.lib import (
    STDOUT,
    CmdResult,
    Pipe,
    Status,
    StatusColor,
    Std,
    _print_title,
    print_status,
)
from cmdi.redirector import no_redirector, redirect_stdfiles


def _get_std(
    std: Union[Pipe, Literal[Std.OUT], None],
) -> Tuple[Union[Pipe, None], Union[IO, None]]:
    if not isinstance(std, Pipe):
        return (None, None)

    if not std.save:
        return (std, None)

    if std.text:
        return (std, io.StringIO())
    else:
        return (std, io.BytesIO())


def _get_redirector(
    stdout_pipe: Optional[Pipe],
    stdout_file: Optional[IO],
    stderr_pipe: Optional[Pipe],
    stderr_file: Optional[IO],
) -> _GeneratorContextManager[None, None, None]:
    if not stdout_pipe and not stderr_pipe:
        return no_redirector()
    else:
        return redirect_stdfiles(stdout_pipe, stdout_file, stderr_pipe, stderr_file)


P = ParamSpec("P")
R = TypeVar("R")


def command(decorated_func: Callable[P, R]) -> Callable[P, CmdResult[R]]:
    """
    The @command decorator that turns a function into a command.
    """

    @wraps(decorated_func)
    def command_wrapper(
        *args,
        _catch_err: bool = True,
        _verbose: bool = True,
        _color: bool = True,
        _stdout: Union[Pipe, None] = None,
        _stderr: Union[Pipe, Literal[Std.OUT], None] = None,
        **kwargs,
    ) -> CmdResult[R]:
        """"""

        name = decorated_func.__name__
        catch_err = _catch_err
        verbose = _verbose
        colorful = _color

        if verbose:
            _print_title(name, color=colorful)

        stdout_pipe, stdout_file = _get_std(_stdout)

        if _stderr == STDOUT:
            # Write into the same file as stdout
            stderr_pipe = deepcopy(stdout_pipe) if stdout_pipe else None
            stderr_file = stdout_file
        else:
            stderr_pipe, stderr_file = _get_std(_stderr)

        with _get_redirector(stdout_pipe, stdout_file, stderr_pipe, stderr_file):
            try:
                cleaned_kwargs = {
                    k: v
                    for k, v in kwargs.items()
                    if k
                    not in ["_stdout", "_stderr", "_catch_err", "_verbose", "_color"]
                }
                item = decorated_func(*args, **cleaned_kwargs)

                # If the user returns a CustomCmdResult, we take it and
                # apply default values if necessary.
                if isinstance(item, CmdResult):
                    value = item.value
                    code = item.code or 0
                    name = item.name or name
                    status = item.status if hasattr(item, "status") else Status.ok
                    color = item.color if hasattr(item, "color") else StatusColor.green

                    result = CmdResult(
                        value=value,
                        code=code,
                        name=name,
                        status=status,
                        color=color,
                    )
                # If the return type is none of CmdResult/CustomCmdResult,
                # we wrap the default CmdResult around the return value.
                else:
                    result = CmdResult(
                        value=item,
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
                    value=None,
                    code=e.returncode,
                    name=name,
                    status=Status.error,
                    color=StatusColor.red,
                )
            except Exception as e:
                print(e, file=sys.stderr)
                if not catch_err:
                    sys.exit(1)
                result = CmdResult(
                    value=None,
                    code=1,
                    name=name,
                    status=Status.error,
                    color=StatusColor.red,
                )

        if isinstance(stdout_file, io.StringIO):
            result.stdout = stdout_file.getvalue()
        elif isinstance(stdout_file, io.BytesIO):
            result.stdout_b = stdout_file.getvalue()

        if isinstance(stderr_file, io.StringIO):
            if not _stderr == STDOUT:
                result.stderr = stderr_file.getvalue()
        elif isinstance(stderr_file, io.BytesIO):
            if not _stderr == STDOUT:
                result.stderr_b = stderr_file.getvalue()

        if verbose:
            print_status(
                result,
                color=colorful,
            )

        # NOTE: The type for 'result.val' could be 'None' here instead of 'R'.
        # We ignore this and trade convenience for safty here. The user should
        # check and handle 'result.code' or use '_catch_err=False' before reading
        # 'result.value'.
        #
        # We prefer this:
        #
        #  if result.code != 0:
        #     handle error...
        #  foo = result.val
        #
        # Over this:
        #
        # if result.code != 0:
        #     handle error...
        # foo = result.value if resul.value else ""
        #
        return result  # type: ignore

    return command_wrapper
