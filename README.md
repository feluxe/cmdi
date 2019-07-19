# cmdi - Command Interface

## Description

A decorator (`@command`) that applies a special interface called the _Command Interface_ to its decorated function. Initially written for the _buildlib_.

The _Command Interface_ allows you to control the exectuion of a function via the _Command Interface_:

-   It allows you to save/redirect output streams (stdout/stderr) for its decorated function.
-   It allows you to catch exceptions for its decorated function and return them with the `CmdResult()`, including _return codes_, _error messages_ and colored _status messages_.
-   It allows you to print status messages and summaries for a command at runtime.
-   And more...

A function that is decorated with `@command` can receive a set of sepcial keyword arguments (`_verbose=...`, `_out=...`, `_err=...`, `catch_err=...`, etc.) and it always returns a `CmdResult()` object.

## Requirements

Python `>= 3.7`

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
def foo_cmd(x, **cmdargs) -> CmdResult:
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
    status='Ok',
    color=0,
    out=None,
    err=None
)
```

### Command Function Arguments

You can define the behaviour of a command function using a set of special keyword argumnets that are applied to the decorated function.

In this example we redirect the output of `foo_cmd` to a custom writer and catch exceptions, the output and information of the exception are then returned with the `CmdResult()` object:

```python
from io import StringIO
from cmdi import CmdResult


result = foo_cmd(10, _out=StringIO(), _catch_err=True)

isinstance(result, CmdResult) # True
```

More on special keyword arguments can be found in the API documentation below.

### Customizing the Result of a command function

A command always returns a `CmdResult` object, for which the `@command` wrapper function automatically guesses the values, which is good enough in many situations. But sometimes you need fine grained control over the output, e.g. to create function specific return codes:

```python
@command
def foo_cmd(x: str, **cmdargs) -> CmdResult:

    print(x)
    somestr = "foo" + x

    if x == "bar":
        code = 0
    else:
        code = 42

    # Customized Result:

    return CmdResult(
        val=somestr,
        code=code,
    )
```

**Note:** In the example above, we return a customized `CmdResult` for which we only customize the fields `val` and `code`. You can customize every field of the `CmdResult` object (optionally). The fields you leave out are set automatically.

### Command Interface Wrappers

Sometimes you want to use the _Command Interface_ for an existing function, without touching the function definition. You can do so by creating a _Command Interface Wrapper_:

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

### Usage with `subprocess`

If you want to use the `@command` decorator on functions that use `subprocess`'es, you have to stick to the following convention, otherwise your command function might not be able to redirect `stdout`/`stderr` to custom IO streams.

First you have to use `Popen()` with the following arguments:

```python
p = subprocess.Popen(
    # ...
    stdout=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    bufsize=1,
)
```

and then you have to write the output of each PIPE to `stdout` and `stderr` manually. `cmdi` offers `read_popen_pipes()` and `resolve_popen()` to help with that.

`cmdi` also provides a function `run_subprocess()` which is similar to `subprocess.run()`. This function runs Popen in a `cmdi` conformable way and returns a `CompletedProcess()` object. See API documentation below.

### Command Interface Wrappers and `subprocess`

If you need to create a _Command Interface Wrapper_ for an existing function that runs a `subprocess` and your command depends on the `returncode` of that, you can use the `subprocess.CalledProcessError` exception to compose something. E.g.:

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

#### Issue with missing Popen output

It can happen that you your Popen command doesn't print/save the command output. In such case you should try to change `bufsize` to `1` or `0`, e.g. `Popen(..., bufzise=1)`.

A known situation where `bufsize=1` won't help is, when you call Python scripts with `Popen`, e.g.:

```python
Popen(['python', 'my_script.py'])
```

To fix this, you have to run Python _unbuffered_ via the `-u` flag:

```python
Popen(['python', '-u', 'my_script.py'])
```

Alternatively you can set the env-var `PYTHONUNBUFFERD=1` for `Popen(..., env=...)`

## API

### decorator `@command`

This decorator allows you to apply the _command interface_ to a function.

A function decorated with `@command` can take the following keyword arguments:

#### `_verbose: bool = True`

Enable/Disable printing of header/status message during runtime.

**Example:**

```python
result = my_command_func("some_arg", _verbose=False)
```

#### `_color: bool = True`

Enable/Disable color for header/status message.

**Example:**

```python
result = my_command_func("some_arg", _color=False)
```

#### `_out: IO = sys.stdout`

Redirect stdout of the child function to a stream object.

**Example:**

```python
import io

result = my_command_func('foo', _out=io.StringIO())

print(result.out.getvalue())
```

#### `_out: IO = sys.stderr`

Redirect stderr of the child function to a stream object.

**Example:**

```python
import io

result = my_command_func('foo', _err=io.StringIO())

print(result.err.getvalue())
```

#### `_catch_err: bool = True`

Catch errors from child function.

This will let the runtime continue, even if a child function throws an exception. The resulting `CmdResult` provides information about the error in `err`, `code` and `status`. The `color` will be set to red.

**Example:**

```python
r = my_command_func("some_arg", _catch_err=True)
```

### dataclass `CmdResult()`

The command result object.

A function decorated with `@command` returns a `CmdResult` object:

```python
@dataclass
class CmdResult:
    val: Optional[Any]
    code: Optional[int]
    name: Optional[str]
    status: Optional[str]
    color: Optional[int]
    out: Optional[TextIO]
    err: Optional[TextIO]
```

def strip*cmdargs(locals*: Dict[str, Any]) -> Dict[str, Any]:

### function `strip_cmdargs()`

**Parameters**

-   `locals_: Dict[str, Any]`

**Returns**

-   `Dict[str, Any]`

Remove cmdargs from locals.
This is useful in case you don't want to decorate a function directly, but maintain a separate command interface for it.

Example usage:

Example usage:

```python
def foo(x):
    # Do a lot of stuff
    return x * 2

@command
def foo_cmd(x, **cmdargs):
    return foo(strip_cmdargs(locals()))
```

### `StdOutIO()` and `StdErrIO()`

Special stream writers.

`cmdi` provides two special stream writers: `StdOutIO` and `StdErrIO`, which mirror output of stdout and stderr to both the default stream writers (`sys.stdout`, `sys.stderr`) and to a `StringIO` stream, thus you can print to the terminal and return output with `CmdResult` at the same time.

-   `StdOutIO` writes _stdout_ to `sys.stdout` and to a `StringIO` object at the same time.
-   `StdErrIO` writes _stderr_ to `sys.stderr` and to a `StringIO` object at the same time.

**Example:**

```python
from cmdi import command, StdOutIO

@command
def foo():
    print('bar')

# This command prints "bar" to the terminal at runtime:
result = foo(_out=StdOutIO())

# The CmdResult contains the output as a string as well, so this line prints
# "bar" as well:
print(result.out.getvalue())
```

### function `print_title()`

**Parameter**

-   `result: CmdResult`
-   `color: bool = True`
-   `file: Optional[IO[str]] = None`

**Returns**

-   `None`

Print the title for a command result

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

### function `print_status()`

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

### function `print_result()`

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

### function `print_summary()`

**Parameter**

-   `results: CmdResult`
-   `color: bool = True`
-   `headline: bool = True`
-   `file: Optional[IO[str]] = None`

**Returns**

-   `None`

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

### function `read_popen_pipes()`

**Parameter**

-   `p: subprocess.Popen`
-   `interval: int = 10` - The interval which the output streams are read and written with.

**Returns**

-   `Iterator[Tuple[str, str]]`

This returns an iterator which returns Popen pipes line by line for both `stdout` and `stderr` in realtime.

**Example usage:**

```python
from cmdi import POPEN_DEFAULTS, read_popen_pipes

p = subprocess.Popen(mycmd, **POPEN_DEFAULTS)

for out_line, err_line in read_popen_pipes:
    print(out_line, end='')
    print(err_line, end='')

code = p.poll()
```

### function `resolve_popen()`

**Parameter**

-   `p: subprocess.Popen`
-   `save_stdout: bool = False` - If set to `True`, the function output is returned.
-   `save_stderr: bool = False` - If set to `True`, the function error output is returned.
-   `mute_stdout: bool = False` - If set to `True`, the function output won't be written to sys.stdout.
-   `mute_stderr: bool = False` - If set to `True`, the function error output won't be written to sys.stderr.
-   `catch: List[int] = []` - Do not raise error for returncodes defined here. You can use `["*"]` to prevent exceptions for all returncodes.
-   `interval: int = 10` - The interval which the output streams are read and written with.

**Returns**

-   `subprocess.CompletedProcess`

Handle running Popen process in a `cmdi` conformable way.

**Example usage:**

```python
from cmdi import POPEN_DEFAULTS, resolve_popen

p = subprocess.Popen(mycmd, **POPEN_DEFAULTS)

# Do stuff with p.

# Get CompletedProcess object.
cp = resolve_popen(p, save_stdout=True, mute_stdout=True)

```

### function `run_subprocess()`

**Parameter**

-   `p: subprocess.Popen`
-   `save_stdout: bool = False` - If set to `True`, the function output is returned.
-   `save_stderr: bool = False` - If set to `True`, the function error output is returned.
-   `mute_stdout: bool = False` - If set to `True`, the function output won't be written to sys.stdout.
-   `mute_stderr: bool = False` - If set to `True`, the function error output won't be written to sys.stderr.
-   `catch: List[int] = []` - Do not raise error for returncodes defined here. You can use `["*"]` to prevent exceptions for all returncodes.
-   `interval: int = 10` - The interval which the output streams are read and written with.
-   `cwd: Optional[str] = None` - See subprocess Popen.
-   `shell: bool = False` - See subprocess Popen.

**Returns**

-   `subprocess.CompletedProcess`

Run Popen process in a `cmdi` conformable way.

**Example usage:**

```python
from cmdi import POPEN_DEFAULTS, run_subprocess

cp = run_subprocess(mycmd, **POPEN_DEFAULTS)
```
