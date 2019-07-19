import pytest
import sys
import subprocess as sp

# Run basic test with pytest

result = pytest.main(['tests/test_basics.py', '-x', '-v'])
result += pytest.main(['tests/test_print_summary.py', '-x', '-v'])

if result > 0:
    sys.exit()

# Run visual tests

sp.run(['python', 'tests/test_visuals.py'])

import cmdi


@cmdi.command
def foo_cmd(**cmdargs):
    code = foo(**cmdi.strip_cmdargs(locals()))


def foo() -> None:

    with sp.Popen(['sh', 'tests/tmp.sh'], **POPEN_DEFAULTS) as p:
        cmdi.print_popen_pipes(p)
        # out, err = cmdi.print_and_save_popen_pipes(p)

        # code = p.wait()
        val = p.communicate()
        print(val)

    # return code


# foo()

print("NEW2")

from cmdi import read_popen_pipes, POPEN_DEFAULTS
import sys

# @command
# def foo2_cmd(**cmdargs):
#     try:
#         return mount_drive(**strip_args(locals()))
#     except sp.CalledProcessError as e:
#         # In case drive is already mounted.
#         if e.returncode == 32:
#             return CmdResult(
#                 code=e.returncode,
#                 status=Status.skip,
#             )
#         else:
#             raise sp.CalledProcessError(e.returncode, [])


def foo2() -> None:

    cmd = ['sh', 'tests/tmp.sh']

    p = sp.Popen(cmd, **POPEN_DEFAULTS)

    for out_line, err_line in read_popen_pipes(p, 15):
        sys.stdout.write(out_line)
        sys.stderr.write(err_line)

    code = p.wait()

    if code != 0:
        raise sp.CalledProcessError(code, cmd)


foo2()


def foo3() -> None:
    cp = cmdi.run_subprocess(
        ['sh', 'tests/tmp.sh'],
        save_stderr=True,  # default: False
        save_stdout=True,  # default: False
        mute_stdout=False,  # default: False
        mute_stderr=True,  # default: False
        catch=[1, 42],  # default: None
    )
    print(cp.stdout)
    print(cp.stderr)


print("RUN 3")

foo3()
