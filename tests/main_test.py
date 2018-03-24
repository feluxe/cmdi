"""

"""

# from cmdinter import run_cmd, CmdFuncResult, CmdResult, Status
import sys
import io
import cmdi
from cmdi import command, CmdResult, set_result
from sty import fg, rs


def _get_title(
    string: str,
    color: bool = True,
):
    sep = '\n' + (len(string) + 5) * '-'
    if color:
        return f'\n{fg.cyan}Cmd: {string}{sep}{fg.rs}'
    else:
        return f'\nCmd: {string}{sep}'


@command
def print_stdout_stderr(
    **cmdargs,
) -> CmdResult:
    """"""
    print('foo stdout')
    print('bar stderr', file=sys.stderr)
    return set_result()


def stage_print_stdout_stderr():
    return print_stdout_stderr()


def test_print_stdout_stderr(capfd):
    func_name = 'print_stdout_stderr'

    result = stage_print_stdout_stderr()

    out, err = capfd.readouterr()

    # Check stdout.
    title: str = _get_title(func_name)
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
    title: str = _get_title(func_name)
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
    title: str = _get_title(func_name, color=False)
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


def stage_verbose_false():
    return print_stdout_stderr(_verbose=False)


def test_verbose_false(capfd):
    func_name = 'print_stdout_stderr'

    result = stage_verbose_false()

    out, err = capfd.readouterr()

    # Check stdout.
    title: str = _get_title(func_name)
    a: str = 'foo stdout\n'
    status: str = f'{fg.green}{func_name}: Ok{fg.rs}'
    assert title not in out
    assert a in out
    assert status not in out

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
