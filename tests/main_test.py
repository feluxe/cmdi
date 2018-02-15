"""

"""

# from cmdinter import run_cmd, CmdFuncResult, CmdResult, Status
import sys
import io
import cmdi
from cmdi import command, CmdResult
from sty import fg, rs


@command
def print_stdout_stderr(
    **cmdargs,
) -> CmdResult:
    """"""
    print('foo stdout')
    print('bar stderr', file=sys.stderr)


def stage_print_stdout_stderr():
    return print_stdout_stderr()


def test_print_stdout_stderr(capfd):
    func_name = 'print_stdout_stderr'

    result = stage_print_stdout_stderr()

    out, err = capfd.readouterr()

    # Check stdout.
    title: str = f'\n{fg.cyan}Run: {func_name}{fg.rs}\n'
    a: str = 'foo stdout\n'
    status: str = f'{fg.green}{func_name}: Ok{fg.rs}'
    assert title in out
    assert a in out
    assert status in out

    # Check stderr.
    a: str = 'bar stderr'
    assert a in err

    # Check result type.
    assert type(result) == cmdi.CmdResult

    # Check result val.
    assert result.val is None

    # Check result status.
    status: str = f'Ok'
    assert result.status == status


def stage_redirect_stdout_stderr_to_io():
    o = io.StringIO()
    e = io.StringIO()
    return print_stdout_stderr(_out=o, _err=e)


def test_redirect_stdout_stderr_to_io(capfd):
    func_name = 'print_stdout_stderr'

    result = stage_redirect_stdout_stderr_to_io()

    out, err = capfd.readouterr()

    # Check stdout and stderr.
    assert out == ''
    assert err == ''

    # Check result type.
    assert type(result) == cmdi.CmdResult

    # Check result val.
    assert result.val is None

    # Check result out.
    title: str = f'\n{fg.cyan}Run: {func_name}{fg.rs}\n'
    a: str = 'foo stdout\n'
    status: str = f'{fg.green}{func_name}: Ok{fg.rs}'
    assert title in result.out.getvalue()
    assert a in result.out.getvalue()
    assert status in result.out.getvalue()

    # Check result err.
    a: str = 'bar stderr'
    assert a in result.err.getvalue()

    # Check result status.
    status: str = f'Ok'
    assert result.status == status


def stage_no_color():
    return print_stdout_stderr(_color=False)


def test_no_color(capfd):
    func_name = 'print_stdout_stderr'

    result = stage_no_color()

    out, err = capfd.readouterr()

    # Check stdout.
    title: str = f'\nRun: {func_name}\n'
    a: str = 'foo stdout\n'
    status: str = f'Ok'
    assert title in out
    assert a in out
    assert status in out

    # Check stderr.
    a: str = 'bar stderr'
    assert a in err

    # Check result type.
    assert type(result) == cmdi.CmdResult

    # Check result val.
    assert result.val is None

    # Check result status.
    assert result.status == status
