import io
from tests import main_test
from cmdi import CmdResult
from sty import fg
from concurrent.futures import ProcessPoolExecutor as Executor, as_completed, wait as f_wait


def print_section(func, label=''):
    print(f'{fg.li_magenta}\n\n{func.__name__} {label}{fg.rs}\n')


def print_flag(string):
    print(fg.da_white + string + fg.rs)


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


print_section(main_test.stage_print_stdout_stderr)
print_flag('[runtime]')
result = main_test.stage_print_stdout_stderr()
print_result(result)

print_section(main_test.stage_redirect_stdout_stderr_to_io)
print_flag('[runtime]')
result = main_test.stage_redirect_stdout_stderr_to_io()
print_result(result)

print_section(main_test.stage_no_color)
print_flag('[runtime]')
result = main_test.stage_no_color()
print_result(result)

print_section(main_test.test_verbose_false)
print_flag('[runtime]')
result = main_test.stage_verbose_false()
print_result(result)

print_section(main_test.stage_print_stdout_stderr, 'Pickle Test')
print_flag('[runtime]')
with Executor() as excecutor:
    future = excecutor.submit(main_test.stage_print_stdout_stderr)
    result = future.result()
    print_result(result)
