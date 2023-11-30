# cmdi - Command Interface


## Description

A decorator `@command` that applies a handy interface called the _Command Interface_ to its decorated function. The _Command Interface_ allows you:

- to save/redirect/mute output streams (stdout/stderr) for its decorated function. This works on file descriptor level. It's possible to redirect output of subprocesses and C code as well.
- to catch exceptions for its decorated function and return them with the `CmdResult()`, including _return codes_, _error messages_ and colored _status messages_.
- to print status messages and summaries for a command at runtime.
- And more...

A function that is decorated with `@command` can receive a set of special keyword arguments (`_verbose=...`, `_stdout=...`, `_stderr=...`, `catch_err=...`, etc.) and it returns a `CmdResult()` object.


## Requirements

Python `>= 3.9`


## Install

```
pip install cmdi
```


## Usage


### The `@command` decorator

Use the `@command` decorator to apply the _command interface_ to a function.

```python
from cmdi import command

@command
def foo_cmd(x, **cmdargs) -> int:
    print(x)
    return x * 2
```

Now you can use `foo_cmd` as a `command`:

```python
result = foo_cmd(10)
```

Which will print the following output (in color):

```
Cmd: foo_cmd
------------
10
foo_cmd: Ok
```

and return a `CmdResult` object:

```python
CmdResult(
    val=20,
    code=0,
    name='foo_cmd',
    status=Status.ok,
    color=StatusColor.green,
    stdout=None,
    stderr=None
)
```


### Command Function Arguments

You can define the behavior of a command function using a set of special keyword arguments that are applied to the decorated function.

In this example we redirect the output of `foo_cmd` to an in-memory file writer and catch exceptions. The output and information of the exception are then returned with the `CmdResult()` object:

```python
from cmdi import CmdResult, Pipe


result = foo_cmd(10, _stdout=Pipe(), _catch_err=True)

isinstance(result, CmdResult) # True

print(result.stdout) # prints caught output.
```

More about special keyword arguments can be found in the API documentation below.


### Customizing the Result of a command function

A command always returns a `CmdResult` object, for which the `@command` wrapper function automatically sets the values for the fields (`code`, `status`, `color`, ...), which is good enough in many situations. But sometimes you need fine grained control over the return values, e.g. to create function specific return codes. In these situations you can explicitly return a `CmdResult` object with some or all of the fields set by yourself:

```python
@command
def foo_cmd(x: str, **cmdargs) -> CmdResult:

    print(x)
    somestr = "foo" + x

    if x == "bar":
        code = 0
    else:
        code = 42

    # Return a customized Command Result:

    return CmdResult(
        val=somestr,
        code=code,
    )
```

**Note:** In the example above, we return a customized `CmdResult` for which we only customize the fields `val` and `code`. You can customize every field of the `CmdResult` object (optionally). The fields you leave out are set automatically.


### Command Interface Function Wrappers

Sometimes you want to use the _Command Interface_ for an existing function, without touching the function definition. You can do so by creating a _Command Interface Function Wrapper_:

```python
from cmdi import command, strip_cmdargs, CmdResult

# This function wraps the Command Interface around an existing function:

@command
def foo_cmd(x, **cmdargs) -> CmdResult:
    return foo(**strip_cmdargs(loclas()))


# The original function that is being wrapped:

def foo(x) -> int:
    print(x)
    return x * 2
```


### Command Interface Function Wrappers and `subprocess` return codes.

If you need to create a _Command Interface Function Wrapper_ for an existing function that runs a `subprocess` and your command depends on the `returncode` of that, you can use the `subprocess.CalledProcessError` exception to compose something. E.g.:

```python
import subprocess as sp
from cmdi import command, CmdResult, Status

@command
def foo_cmd(x, **cmdargs) -> CmdResult:

    try:
        return foo(**strip_cmdargs(locals()))

    except sp.CalledProcessError as e:

        if e.returncode == 13:
            return CmdResult(
                code=e.returncode,
                status=Status.ok,
            )
        elif e.returncode == 42:
            return CmdResult(
                code=e.returncode,
                status=Status.skip,
            )
        else:
            raise sp.CalledProcessError(e.returncode, e.args)


def foo(x) -> int:
    return sp.run(["my_arg"], check=True, ...)

```


## API

### decorator `@command`

This decorator allows you to apply the _command interface_ to a function.

A function decorated with `@command` can take the following keyword arguments:


#### `_verbose: bool = True`

Enable/Disable printing of command header and status information during runtime.

**Example:**

```python
result = my_command_func("some_arg", _verbose=False)
```


#### `_color: bool = True`

Enable/Disable color for command header and status information.

**Example:**

```python
result = my_command_func("some_arg", _color=False)
```


#### `_stdout: Optional[Pipe] = None`

Redirect stdout of the child function. More on `Pipe()` below.

**Example:**

```python
from cmdi import Pipe

pipe = Pipe(text=False, tty=True, ...) # See Pipe doc for arguments...

result = my_command_func('foo', _stdout=pipe)

print(result.stdout) # Prints the caught ouput.
```


#### `_stderr: Union[Optional[Pipe], STDOUT] = None`

Redirect stderr of the child function. More on `Pipe()` below.

**Example:**

```python
from cmdi import Pipe

pipe = Pipe(text=False, tty=True, ...) # See Pipe doc for arguments...

result = my_command_func('foo', _stderr=pipe))

print(result.stderr) # Prints the caught ouput.
```

If you want to redirect `stderr` to `stdout`, you can use this:

```python
from cmdi import STDOUT

result = my_command_func('foo', _stderr=STDOUT))
```


#### `_catch_err: bool = True`

Catch errors from child function.

This will let the runtime continue, even if a child function throws an exception. If an exception occurs the `CmdResult` object will provide information about the error at `result.stderr`, `result.code` and `result.status`. The status message will appear in red.

**Example:**

```python
from cmdi import Pipe

r = my_command_func("some_arg", _catch_err=True, _stderr=Pipe())

r.status # Error
r.code # 1
r.stdout # The stderr output from the function call.

```


### class `CmdResult()`

The command result object.

A function decorated with `@command` returns a `CmdResult` object:

```python
class CmdResult:
    val: T, # The return value of the wrapped function.
    code: int, # Return code
    name: str, # Command name. By default the name of the wrapped function.
    status: Optional[Status],
    color: Optional[StatusColor],
    stdout: Optional[Union[str, bytes]] = None,
    stderr: Optional[Union[str, bytes]] = None,
```


### dataclass `Pipe()`

Use this type to configure `stdout`/`stderr` for a command call.

**Parameters**

- `save: bool = True` - Save the function output if `True`.
- `text: bool = True` - Save function output as text if `True` else save as bytes.
- `dup: bool = False` - Redirect output at file descriptor level if `True`. This allows you to redirect output of subprocesses and C code. It's *dup* because we're duping file descriptors.
- `tty: bool = False` - Keep ANSI sequences for saved output if `True`, else strip ANSI sequences.
- `mute: bool = False` - Mute output of function call in terminal if `True`. NOTE: You can still save and return the output if this is enabled.

**Example:**

```python
from cmdi import CmdResult, Pipe

out_pipe = Pipe(text=False, dup=True, mute=True)
err_pipe = Pipe(text=False, dup=True, mute=False)

result = foo_cmd(10, _stdout=out_pipe, _stderr=err_pipe, _catch_err=True)

print(result.stdout) # prints caught output.
print(result.stderr) # prints caught output.
```


### Redirect output of functions that run subprocesses or external/foreign/C code.

If you want to redirect the output of a function that runs a subprocess or calls foreign code, you have to use a `Pipe` with the argument `dup=True`. This will catch the output of stdout/stderr at a lower level (by duping file descriptors):

```python
import subprocess
from cmdi import command, Pipe

@command
def foo(x, **cmdargs) -> CmdResult:
    subprocess.run("my_script")

# Catch stdout of the function via low level redirect:
foo(_stdout=Pipe(dup=True))
```


### function `strip_cmdargs(locals_)`

**Parameters**

- `locals_: Dict[str, Any]`

**Returns**

- `Dict[str, Any]`

Remove cmdargs from dictionary.
This function helps us to easily create _Command Interface Function Wrappers_.

Example usage:

```python
def foo(x):
    # Do a lot of stuff
    return x * 2

@command
def foo_cmd(x, **cmdargs):
    return foo(strip_cmdargs(locals()))
```


### function `print_title(result, color, file)`

**Parameter**

-   `result: CmdResult`
-   `color: bool = True`
-   `file: Optional[IO[str]] = None`

**Returns**

-   `None`

Print the title for a command result.

**Example usage:**

```python
result = my_cmd('foo')

print_title(result)
```

Output:

```
Cmd: my_cmd
-----------
```


### function `print_status(result, color, file)`

**Parameter**

-   `result: CmdResult`
-   `color: bool = True`
-   `file: Optional[IO[str]] = None`

**Returns**

-   `None`

Print the status of a command result.

**Example usage:**

```python
result = my_cmd('foo')

print_status(result)
```

Output:

```
my_cmd: Ok
```


### function `print_result(result, color, file)`

**Parameter**

-   `result: CmdResult`
-   `color: bool = True`
-   `file: Optional[IO[str]] = None`

**Returns**

-   `None`

Print out the CmdResult object.

**Example usage:**

```python
result = my_cmd('foo')

print_result(result)
```

Output:

```
Cmd: my_cmd
-----------
Stdout:
Runtime output of my_cmd...
Stderr:
Some err
foo_cmd3: Ok
```


### function `print_summary(results, color, headline, file)`

**Parameter**

-   `results: CmdResult`
-   `color: bool = True`
-   `headline: bool = True`
-   `file: Optional[IO[str]] = None`

**Returns**

-   `None`

Print out a summary of one or more command results.

**Example usage:**

```python
from cmdi import print_summary

results = []

results.append(my_foo_cmd())
results.append(my_bar_cmd())
results.append(my_baz_cmd())

print_summary(results)
```

Output:

```
Cmd: my_foo_cmd
---------------
stdout of foo function...
my_foo_cmd: Ok

Cmd: my_bar_cmd
---------------
stdout of bar function...
my_bar_cmd: Ok

Cmd: my_baz_cmd
---------------
stdout of baz function...
my_baz_cmd: Ok
```


### function `read_popen_pipes(p, interval)`

**Parameter**

-   `p: subprocess.Popen`
-   `interval: int = 10` - The interval which the output streams are read and written with.

**Returns**

-   `Iterator[Tuple[str, str]]`

This creates an iterator which returns Popen pipes line by line for both `stdout` and `stderr` separately in realtime.

**Example usage:**

```python
from cmdi import POPEN_DEFAULTS, read_popen_pipes

p = subprocess.Popen(mycmd, **POPEN_DEFAULTS)

for out_line, err_line in read_popen_pipes:
    print(out_line, end='')
    print(err_line, end='')

code = p.poll()
```


## Development / Testing

Run Tests for this library

NOTE: Some test results must be read visually by the human user.

```
poetry run pytest --capture=no tests
```
