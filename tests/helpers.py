import sys
import subprocess as sp
from cmdi import command, CmdResult, strip_cmdargs
from sty import fg


def _title(
    string: str,
    color: bool = True,
):
    sep = '\n' + (len(string) + 5) * '-'
    if color:
        return f'\n{fg.cyan}Cmd: {string}{sep}{fg.rs}'
    else:
        return f'\nCmd: {string}{sep}'


def _status(name):
    return f'{fg.green}{name}: Ok{fg.rs}'


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
    sys.stderr.write(f'stderr_text\n')

    sys.stdout.write(f'{fg.magenta}stdout_ansi_text{fg.rs}\n')
    sys.stderr.write(f'{fg.magenta}stderr_ansi_text{fg.rs}\n')

    if with_sub:
        sp.run(['sh', 'echo.sh'], cwd='./tests', check=True)

    if raise_err:
        1 + ''  # type: ignore

    return return_val
