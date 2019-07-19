# from cmdinter import run_cmd, CmdFuncResult, CmdResult, Status
import sys
import io
import cmdi
from cmdi import command, CmdResult
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


class cmd:

    @staticmethod
    @command
    def dummy_command(foo, **cmdargs) -> CmdResult:
        """"""
        return dummy_command(foo)  # type: ignore


def dummy_command(foo) -> None:
    """"""
    print('foo stdout')
    print('bar stderr', file=sys.stderr)


def test_print_stdout_stderr(capfd):

    result = cmd.dummy_command('foo')

    out, err = capfd.readouterr()

    # Check stdout.
    title: str = _get_title(dummy_command.__name__)
    a: str = 'foo stdout\n'
    status: str = f'{fg.green}{dummy_command.__name__}: Ok{fg.rs}'
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


def test_redirect_stdout_stderr_to_io(capfd):

    result = cmd.dummy_command(
        'foo', _out=io.StringIO(), _err=io.StringIO(), _verbose=False
    )

    out, err = capfd.readouterr()

    # Check stdout and stderr.
    assert out == ''
    assert err == ''

    # Check result type.
    assert type(result) == cmdi.CmdResult

    # Check result val.
    assert result.val is None

    # Check result out.
    title: str = _get_title(dummy_command.__name__)
    a: str = 'foo stdout\n'
    status: str = f'{fg.green}{dummy_command.__name__}: Ok{fg.rs}'
    assert a in result.out.getvalue()

    # Check result err.
    a: str = 'bar stderr'
    assert a in result.err.getvalue()

    # Check result status.
    status: str = f'Ok'
    assert result.status == status


def test_no_color(capfd):

    result = cmd.dummy_command('foo', _color=False)

    out, err = capfd.readouterr()

    # Check stdout.
    title: str = _get_title(dummy_command.__name__, color=False)
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


def test_verbose_false(capfd):

    result = cmd.dummy_command('foo', _verbose=False)

    out, err = capfd.readouterr()

    # Check stdout.
    title: str = _get_title(dummy_command.__name__)
    a: str = 'foo stdout\n'
    status: str = f'{fg.green}{dummy_command.__name__}: Ok{fg.rs}'
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
