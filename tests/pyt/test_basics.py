# from cmdinter import run_cmd, CmdFuncResult, CmdResult, Status
from sty import fg

from cmdi import CmdResult, Status, print_summary
from cmdi.lib import StatusColor

from ..helpers import cmd_print_stdout_stderr, status, title


def test_return_type():
    cr = cmd_print_stdout_stderr()
    assert isinstance(cr, CmdResult)


def test_return_val_none():
    cr = cmd_print_stdout_stderr()
    assert cr.value is None


def test_return_val_str():
    cr = cmd_print_stdout_stderr(return_val="foo")
    assert cr.value == "foo"


def test_return_val_int():
    cr = cmd_print_stdout_stderr(return_val=1)
    assert cr.value == 1


def test_return_status_ok():
    cr = cmd_print_stdout_stderr(1)
    assert cr.status == Status.ok


def test_return_status_error():
    cr = cmd_print_stdout_stderr(raise_err=True)
    assert cr.status == Status.error


def test_print_stdout_stderr(capfd):
    _cr = cmd_print_stdout_stderr()

    stdout, stderr = capfd.readouterr()

    # Test stdout.
    assert (
        title(
            cmd_print_stdout_stderr.__name__,
        )
        in stdout
    )
    assert "stdout_text\n" in stdout
    assert status(cmd_print_stdout_stderr.__name__) in stdout

    # Test stderr.
    assert "stderr_text\n" in stderr


def test_verbose_true(capfd):
    _cr = cmd_print_stdout_stderr(_verbose=True)

    stdout, _stderr = capfd.readouterr()

    # Check stdout and stderr.
    assert title(cmd_print_stdout_stderr.__name__) in stdout
    assert "stdout_text\n" in stdout
    assert status(cmd_print_stdout_stderr.__name__) in stdout


def test_verbose_false(capfd):
    _cr = cmd_print_stdout_stderr(_verbose=False)

    stdout, _stderr = capfd.readouterr()

    # Check stdout and stderr.
    assert fg.cyan not in stdout
    assert "stdout_text\n" in stdout
    assert fg.green and fg.red not in stdout


def test_color_true(capfd):
    _cr = cmd_print_stdout_stderr(_color=True)

    stdout, _stderr = capfd.readouterr()

    # Check stdout and stderr.
    assert fg.cyan in stdout
    assert "stdout_text\n" in stdout
    assert fg.green in stdout


def test_color_false(capfd):
    _cr = cmd_print_stdout_stderr(_color=False)

    stdout, _stderr = capfd.readouterr()

    # Check stdout and stderr.
    assert fg.cyan not in stdout
    assert "stdout_text\n" in stdout
    assert fg.green not in stdout


def test_return_out_none(capfd):
    cr = cmd_print_stdout_stderr("foo")
    assert cr.stdout == ""
    assert cr.stdout_b == b""


def test_return_err_none(capfd):
    cr = cmd_print_stdout_stderr("foo")
    assert cr.stderr == ""
    assert cr.stderr_b == b""


def test_print_summary(capfd):
    result = CmdResult(
        value="foo",
        code=1,
        name="foo",
        status=Status.error,
        color=StatusColor.red,
        stdout="",
        stderr="",
    )

    print_summary(result, color=False)
    print_summary([result, result, None], color=False)

    stdout, _stderr = capfd.readouterr()

    assert "Summary\n-------\nfoo: Error" in stdout
    assert "Summary\n-------\nfoo: Error\nfoo: Error" in stdout
