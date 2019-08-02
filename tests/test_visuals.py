import sys
sys.path.insert(0, '.')
import io
from cmdi import CmdResult, command, Pipe
from sty import fg
from concurrent.futures import ProcessPoolExecutor as Executor, as_completed, wait as f_wait

from tests.helpers import cmd_print_stdout_stderr

# HELPERS
# -------


def print_testname(name, label=''):
    print(f'{fg.li_magenta}\n\n{name} {label}\n{"="*50}{fg.rs}')


def print_flag(string):
    print('\n' + fg.da_white + string + fg.rs)


def print_runtime_flag():
    print_flag('[runtime output]')


def print_result_flag(field):
    print_flag(f'[result.{field}]')


def print_msg(text):
    print(f"{fg.da_white}{text}{fg.rs}")


# TESTS
# -----

print(fg.li_yellow)
print("--------------------------------------------")
print("VISUAL TESTS PLEASE READ THE TERMINAL OUTPUT")
print("--------------------------------------------")
print(
    "We use visual tests for the things in cmdi that we can't test with pytest."
)
print("You must read the below terminal output carefully.")
print("--------------------------------------------")
print(fg.rs)


def test_stdout_stderr():
    print_testname(test_stdout_stderr.__name__)

    print_runtime_flag()
    print_msg("* Should be in color.")
    print_msg("* Should contain stdout and stderr messages.")
    print_msg("* Should contain title and status.")

    cr = cmd_print_stdout_stderr(return_val='foo')

    print_result_flag('val')
    print_msg("* Should be `foo`")
    print(cr.val)


test_stdout_stderr()


def test_pipe_dup_save_text_tty():
    print_testname(test_pipe_dup_save_text_tty.__name__)

    print_runtime_flag()
    print_msg("* Should be in color.")
    print_msg("* Should contain title and status.")
    print_msg("* Should contain stdout and stderr messages.")
    print_msg("* Should contain stdout and stderr of subprocess as well.")

    p = Pipe(dup=True, save=True, tty=True, text=True)

    cr = cmd_print_stdout_stderr(
        return_val='foo', with_sub=True, _stdout=p, _stderr=p
    )

    print_result_flag('out')
    print_msg("* Should contain all stdout lines in color.")
    print_msg("* Should contain stdout and stderr of subprocess as well.")
    print(cr.stdout)

    print_result_flag('err')
    print_msg("* Should contain all stderr lines in color.")
    print_msg("* Should contain stdout and stderr of subprocess as well.")
    print(cr.stderr)


test_pipe_dup_save_text_tty()


def test_pipe_dup_mute():
    print_testname(test_pipe_dup_mute.__name__)

    print_runtime_flag()
    print_msg("* Should only show title and status in color.")

    p = Pipe(dup=True, save=True, tty=True, text=True, mute=True)

    cr = cmd_print_stdout_stderr(
        return_val='foo', with_sub=True, _stdout=p, _stderr=p
    )

    print_result_flag('out')
    print_msg("* Should contain all stdout lines in color.")
    print_msg("* Should contain stdout and stderr of subprocess as well.")
    print(cr.stdout)

    print_result_flag('err')
    print_msg("* Should contain all stderr lines in color.")
    print_msg("* Should contain stdout and stderr of subprocess as well.")
    print(cr.stderr)


test_pipe_dup_mute()


def test_pickle():
    print_testname(test_pickle.__name__)
    print_runtime_flag()
    print_msg("* Should be in color.")
    print_msg("* Should contain title and status.")
    print_msg("* Should contain stdout and stderr messages.")
    print_msg("* Should contain stdout and stderr of subprocess as well.")

    p = Pipe(dup=True, save=True, tty=True, text=True, mute=False)

    with Executor() as excecutor:
        future = excecutor.submit(
            cmd_print_stdout_stderr, 'foo', with_sub=True, _stdout=p, _stderr=p
        )
        cr = future.result()

    print_result_flag('out')
    print_msg("* Should contain all stdout lines in color.")
    print_msg("* Should contain stdout and stderr of subprocess as well.")
    print(cr.stdout)

    print_result_flag('err')
    print_msg("* Should contain all stderr lines in color.")
    print_msg("* Should contain stdout and stderr of subprocess as well.")
    print(cr.stderr)


test_pickle()
