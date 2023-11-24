from cmdi import Pipe, STDOUT
from sty import fg

from ..helpers import cmd_print_stdout_stderr, _title, _status

# Dup = False
# -----------


def test_tty_true(capfd):
    p = Pipe(dup=False, save=True, mute=False, text=True, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=False, _stdout=p, _stderr=p)

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in cr.stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in cr.stderr


def test_tty_false(capfd):
    p = Pipe(dup=False, save=True, mute=False, text=True, tty=False)

    cr = cmd_print_stdout_stderr(with_sub=False, _stdout=p, _stderr=p)

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert f"stdout_ansi_text\n" in cr.stdout
    assert f"stderr_ansi_text\n" in cr.stderr


def test_text_true(capfd):
    p = Pipe(dup=False, save=True, mute=False, text=True, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=False, _stdout=p, _stderr=p)

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in cr.stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in cr.stderr


def test_text_false(capfd):
    p = Pipe(dup=False, save=True, mute=False, text=False, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=False, _stdout=p, _stderr=p)

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert b"stdout_text" in cr.stdout
    assert b"stderr_text" in cr.stderr


def test_mute_true(capfd):
    p = Pipe(dup=False, save=True, mute=True, text=True, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=False, _stdout=p, _stderr=p, _verbose=False)

    stdout, stderr = capfd.readouterr()

    assert stdout == ""
    assert stderr == ""
    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in cr.stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in cr.stderr


# Dup = True
# ----------
# NOTE: Unfortunately capturing output via pytest's `capfd` conflicts with cmdi's
# `dup=True`.
# NOTE: You should also run pytest with --capture=no flag if you want to test dup=True.


def test_dup_subprocess_output_exists():
    p = Pipe(dup=True, save=True, mute=False, text=True, tty=False)

    cr = cmd_print_stdout_stderr(with_sub=True, _stdout=p, _stderr=p)

    assert "stdout_text\n" in cr.stdout
    assert "subprocess: stdout_text 1\n" in cr.stdout
    assert "subprocess: stderr_text" in cr.stderr


def test_dup_tty_true(capfd):
    p = Pipe(dup=True, save=True, mute=False, text=True, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=True, _stdout=p, _stderr=p)

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in cr.stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in cr.stderr


def test_dup_tty_false(capfd):
    p = Pipe(dup=True, save=True, mute=False, text=True, tty=False)

    cr = cmd_print_stdout_stderr(with_sub=True, _stdout=p, _stderr=p)

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert f"stdout_ansi_text\n" in cr.stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert f"stderr_ansi_text\n" in cr.stderr


def test_dup_text_true(capfd):
    p = Pipe(dup=True, save=True, mute=False, text=True, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=True, _stdout=p, _stderr=p)

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in cr.stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in cr.stderr


def test_dup_text_false(capfd):
    p = Pipe(dup=True, save=True, mute=False, text=False, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=True, _stdout=p, _stderr=p)

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert b"stdout_text" in cr.stdout
    assert b"stderr_text" in cr.stderr


def test_redirect_stderr_to_stdout():
    p = Pipe(dup=True, save=True, mute=False, text=True, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=True, _stdout=p, _stderr=STDOUT)

    assert cr.stderr is None
    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in cr.stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in cr.stdout
