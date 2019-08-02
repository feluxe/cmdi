"""
You can use this test module to fiddle with cmdi.

You can run it with:

    pipenv run python tests/test_fiddle.py

"""
import sys
sys.path.insert(0, '.')
from cmdi import *
from sty import fg
import subprocess as sp


@command
def cmd_print_stdout_stderr(
    return_val=None,
    raise_err=False,
    with_sub=False,
    **cmdargs,
) -> CmdResult:
    """
    A dummy command that is used in several tests.
    """
    return print_stdout_stderr(**strip_cmdargs(locals()))  # type: ignore


def print_stdout_stderr(
    return_val=None,
    raise_err=False,
    with_sub=False,
) -> None:
    """
    A dummy function that is used in several tests.
    """
    sys.stdout.write(f'stdout_text\n')
    sys.stdout.write(f'stdout_text\n')
    sys.stdout.write(f'stdout_text\n')
    # '' + 1
    sys.stderr.write(f'stderr_text\n')
    sys.stderr.write(f'stderr_text\n')
    sys.stderr.write(f'stderr_text\n')

    sys.stdout.write(f'{fg.magenta}stdout_ansi_text{fg.rs}\n')
    sys.stderr.write(f'{fg.magenta}stderr_ansi_text{fg.rs}\n')

    if with_sub:
        sp.run(['sh', 'echo.sh'], cwd='./tests', check=True)

    if raise_err:
        1 + ''  # type: ignore

    return return_val


p = Pipe(dup=True, save=True, mute=True, text=True, tty=True)

# cr = cmd_print_stdout_stderr(with_sub=True, _out=p, _err=p, _verbose=False)
cr = cmd_print_stdout_stderr(with_sub=True, _stdout=p, _stderr=STDOUT, _verbose=True)

print("\nOUT:")
print(cr.stdout)
print("\nERR:")
print(cr.stderr)
