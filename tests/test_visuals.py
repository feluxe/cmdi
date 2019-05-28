import io
import sys
from cmdi import CmdResult, command
from sty import fg
from concurrent.futures import ProcessPoolExecutor as Executor, as_completed, wait as f_wait


def print_testname(name, label=''):
    print(f'{fg.li_magenta}\n\nTest: {name} {label}{fg.rs}\n')


def print_flag(string):
    print(fg.da_white + string + fg.rs)


class cmd:

    @staticmethod
    @command
    def dummy_command(foo, **cmdargs) -> CmdResult:
        """"""
        return dummy_command(foo)


def dummy_command(foo) -> None:
    """"""
    print('foo stdout')
    print('bar stderr', file=sys.stderr)


def print_result(result):
    if not isinstance(result, CmdResult):
        return
    print_flag('[result.val]')
    print(result.val)
    print_flag('[result.status]')
    print(result.status)
    try:
        print_flag('[result.out]')
        print(result.out.getvalue())
    except AttributeError:
        pass
    try:
        print_flag('[result.err]')
        print(result.err.getvalue())
    except AttributeError:
        pass


print_testname("Stdout/stderr")
print_flag('[runtime]')
result = cmd.dummy_command('foo')
print_result(result)

print_testname("Redirect stdout/stderr to io")
print_flag('[runtime]')
o = io.StringIO()
e = io.StringIO()
result = cmd.dummy_command('foo', _out=o, _err=e)
print_result(result)

print_testname("Color=False")
print_flag('[runtime]')
result = cmd.dummy_command('foo', _color=False)
print_result(result)

print_testname('Verbose=False')
print_flag('[runtime]')
result = cmd.dummy_command('foo', _verbose=False)
print_result(result)

print_testname('Pickle')
print_flag('[runtime]')
with Executor() as excecutor:
    future = excecutor.submit(cmd.dummy_command, 'foo')
    result = future.result()
    print_result(result)
