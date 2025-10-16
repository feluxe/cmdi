from sty import fg

from cmdi import STDOUT, Pipe

from ..helpers import cmd_print_stdout_stderr

# Fd = False
# -----------


def test_tty_true(capfd):
    p = Pipe(fd=False, save=True, mute=False, text=True, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=False, _stdout=p, _stderr=p)

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in cr.stdout

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in cr.stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in cr.stderr


def test_tty_false(capfd):
    p = Pipe(fd=False, save=True, mute=False, text=True, tty=False)

    cr = cmd_print_stdout_stderr(with_sub=False, _stdout=p, _stderr=p)

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert "stdout_ansi_text\n" in cr.stdout
    assert "stderr_ansi_text\n" in cr.stderr


def test_text_true(capfd):
    p = Pipe(fd=False, save=True, mute=False, text=True, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=False, _stdout=p, _stderr=p)

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in cr.stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in cr.stderr


def test_text_false(capfd):
    p = Pipe(fd=False, save=True, mute=False, text=False, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=False, _stdout=p, _stderr=p)

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert b"stdout_text" in cr.stdout_b
    assert b"stderr_text" in cr.stderr_b


def test_mute_true(capfd):
    p = Pipe(fd=False, save=True, mute=True, text=True, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=False, _stdout=p, _stderr=p, _verbose=False)

    stdout, stderr = capfd.readouterr()

    assert stdout == ""
    assert stderr == ""
    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in cr.stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in cr.stderr


# Fd = True
# ----------
# NOTE: Unfortunately capturing output via pytest's `capfd` conflicts with cmdi's
# `fd=True`.
# NOTE: You should also run pytest with --capture=no flag if you want to test fd=True.


def test_fd_subprocess_output_exists():
    p = Pipe(fd=True, save=True, mute=False, text=True, tty=False)

    cr = cmd_print_stdout_stderr(with_sub=True, _stdout=p, _stderr=p)

    assert "stdout_text\n" in cr.stdout
    assert "subprocess: stdout_text 1\n" in cr.stdout
    assert "subprocess: stderr_text" in cr.stderr


def test_fd_tty_true(capfd):
    p = Pipe(fd=True, save=True, mute=False, text=True, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=True, _stdout=p, _stderr=p)

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in cr.stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in cr.stderr


def test_fd_tty_false(capfd):
    p = Pipe(fd=True, save=True, mute=False, text=True, tty=False)

    cr = cmd_print_stdout_stderr(with_sub=True, _stdout=p, _stderr=p)

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert "stdout_ansi_text\n" in cr.stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert "stderr_ansi_text\n" in cr.stderr


def test_fd_text_true(capfd):
    p = Pipe(fd=True, save=True, mute=False, text=True, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=True, _stdout=p, _stderr=p)

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in cr.stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in cr.stderr


def test_fd_text_false(capfd):
    p = Pipe(fd=True, save=True, mute=False, text=False, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=True, _stdout=p, _stderr=p)

    stdout, stderr = capfd.readouterr()

    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in stderr
    assert cr.stdout == ""
    assert cr.stderr == ""
    assert b"stdout_text" in cr.stdout_b
    assert b"stderr_text" in cr.stderr_b


def test_redirect_stderr_to_stdout():
    p = Pipe(fd=True, save=True, mute=False, text=True, tty=True)

    cr = cmd_print_stdout_stderr(with_sub=True, _stdout=p, _stderr=STDOUT)

    assert cr.stderr == ""
    assert cr.stderr_b == b""
    assert f"{fg.magenta}stdout_ansi_text{fg.rs}\n" in cr.stdout
    assert f"{fg.magenta}stderr_ansi_text{fg.rs}\n" in cr.stdout
