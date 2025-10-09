from sty import fg
from typing_extensions import Unpack

from cmdi import CmdArgs, command

print(fg.li_yellow)
print("--------------------------------------------")
print("EDITOR TEST: Open editor to see if type checker complains")
print("--------------------------------------------")
print("I was to lazy to write acutal test for this.")
print("Just open the test file and see if the type checker complains in your editor.")
print("--------------------------------------------")
print(fg.rs)


def lib_str_function(a: str) -> str:
    return a + "bar"


@command
def cmd_lib_str_function(
    a: str,
    **cmdargs: Unpack[CmdArgs],
) -> str:
    return lib_str_function(a)


def test_typing_generic_cmd_result_value_str():
    result = cmd_lib_str_function("foo")
    if result.value is not None:
        # The type checker should know that result.value is of type string
        print(result.value + "nice")


def lib_int_function(a: int) -> int:
    return a + 2


@command
def cmd_lib_int_function(
    a: int,
    **cmdargs,
) -> int:
    return lib_int_function(a, **cmdargs)


def test_typing_generic_cmd_result_value_int():
    result = cmd_lib_int_function(1)
    if result.value is not None:
        # The type checker should know that result.value is of type string
        print(result.value + 3)
