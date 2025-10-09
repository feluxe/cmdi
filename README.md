# cmdi - Command Interface

## Release 3.0.0 (October 09, 2025)

This is a major release with breaking changes. `cmdi` follows *semver*. If you don't want to upgrade, you can stay on `2.x.x`, which has proven stable for most use cases.

Breaking Changes:

- Renamed `Pipe.dup` to `Pipe.fd` for redirecting output at the file descriptor level.
- Renamed `CmdResult.val` to `CmdResult.value`.
- Improved `CmdResult` handling for `str` vs `bytes` output:
  - Previously: `CmdResult.stdout` and `CmdResult.stderr`
  - Now: For string output: `CmdResult.stdout`, `CmdResult.stderr`; for bytes output: `CmdResult.stdout_b`, `CmdResult.stderr_b`.

Other Changes:

- Added `CmdArgs` for better argument typing.
- Completed typing (should be 100% now).
- Stricter type checking.
- More docstrings.
- Refactored code.
- Removed wildcard imports.
- And maybe more.

# Can you generate a simple index with links to the sections ai!

## Description

`cmdi` provides a powerful Python decorator, `@command`, that transforms ordinary functions into robust, user-friendly command interfaces. With `cmdi`, you can:

- Seamlessly capture, redirect, or mute standard output and error streams (stdout/stderr) at the file descriptor level (including output from subprocesses and C extensions).
- Automatically catch exceptions and return structured results via the `CmdResult` object, which includes return codes, error messages, and color-coded status indicators.
- Effortlessly print status messages and summaries for commands at runtime, making it easy to monitor and debug command execution.
- Pass special keyword arguments (such as `_verbose`, `_stdout`, `_stderr`, `_catch_err`, and more) to control command behavior and output handling.
- Integrate with existing functions or subprocess-based workflows without modifying their core logic.

By decorating a function with `@command`, you enable advanced output management, error handling, and result reporting—all with minimal code changes. The decorated function always returns a `CmdResult` object, providing a consistent and informative interface for downstream processing or user feedback.


## Requirements

Python `>= 3.9`


## Install

```
pip install cmdi
```


## Usage


### The `@command` decorator

The `@command` decorator is the core of `cmdi`. It transforms a regular Python function into a robust command with advanced output handling, error reporting, and status messaging, without changing your function’s logic.

#### Basic Example

```python
from cmdi import command, CmdArgs
from typing import Unpack

@command
def my_square_cmd(x: int, **cmdargs: Unpack[CmdArgs]) -> int:
    y = x * x
    print(f"Square: {y}")
    return y
```

You can now call `my_square_cmd` as a command:

```python
result = my_square_cmd(2)
```

This will print (with color in the terminal):

```
Cmd: my_square_cmd
------------
Square: 4
my_square_cmd: Ok
```

and return a `CmdResult` object with detailed information:

```python
CmdResult(
    value=4,
    code=0,
    name='my_square_cmd',
    status=Status.ok,
    color=StatusColor.green,
    stdout="Square: 4\n",
    stderr="",
    stdout_b=b"",
    stderr_b=b"",
)
```

#### Why use `@command`?

- **Consistent Output:** All decorated functions return a `CmdResult` object, making it easy to handle results programmatically.
- **Flexible Output Handling:** Effortlessly capture, redirect, or mute stdout/stderr, even for subprocesses or C extensions.
- **Automatic Error Handling:** Exceptions are caught and reported in the result, with return codes and status.
- **Status Messaging:** Built-in support for printing command headers, status, and summaries, with optional color.

See below for more advanced usage and customization options.


### Command Function Arguments

You can control the behavior of a command function using a set of special keyword arguments, which are automatically recognized by the `@command` decorator. These arguments let you customize output handling, error catching, and runtime messaging—without changing your function’s core logic.

#### Example: Redirecting Output and Catching Errors

In this example, we redirect the output of `my_square_cmd` to an in-memory pipe and enable exception catching. The output and any exception information are returned in the resulting `CmdResult` object:

```python
from cmdi import command, CmdArgs, Pipe, CmdResult
from typing import Unpack

@command
def my_square_cmd(x: int, **cmdargs: Unpack[CmdArgs]) -> int:
    y = x * x
    print(f"Square: {y}")
    return y

result = my_square_cmd(2, _stdout=Pipe(), _catch_err=True)

assert isinstance(result, CmdResult)  # True

print(result.stdout)  # prints 'Square: 4'
```

#### Available Special Arguments

You can use the following special keyword arguments to control command behavior:

- `_catch_err`: Catch exceptions and return error info in the result.
- `_verbose`: Enable or disable printing of command headers and status.
- `_color`: Enable or disable colored output.
- `_stdout=Pipe(...)`: Redirect or capture standard output.
- `_stderr=Pipe(...)`: Redirect or capture standard error.

`Pipe` objects allow you to mute, redirect, or capture the standard and error output of a function in flexible ways—including at the file descriptor level for subprocesses or C extensions.

See the API documentation below for more details on these arguments and their options.

### Customizing the Result of a Command Function

By default, a function decorated with `@command` returns a `CmdResult` object whose fields (such as `code`, `status`, `color`, etc.) are set automatically based on the function's execution. This is sufficient for most use cases. However, if you need more granular control—such as setting custom return codes, statuses, or other fields—you can explicitly return a `CmdResult` from your function.

#### Example: Returning a Custom `CmdResult`

```python
from cmdi import command, CmdResult, CmdArgs
from typing import Unpack

@command
def my_foo_cmd(x: str, **cmdargs: Unpack[CmdArgs]) -> CmdResult:
    print(x)
    somestr = "foo" + x

    # Set a custom return code based on input
    code = 0 if x == "bar" else 42

    # Return a customized CmdResult
    return CmdResult(
        value=somestr,
        code=code,
        # You can also set status, color, stdout, stderr, etc. if needed
    )
```

**Tip:**  
You only need to specify the fields you want to customize in the `CmdResult`. Any fields you leave out will be set automatically by the command interface.

This approach is useful when you want to:

- Return specific exit codes for different conditions.
- Set custom status or color for the result.
- Attach additional output or error information.
- Integrate with existing error-handling or reporting logic.

### Command Interface Function Wrappers

You may want to apply the _Command Interface_ to an existing function without modifying its original definition. This is easy to do by creating a wrapper function that delegates to the original, while adding the `@command` decorator and handling special command arguments.

#### Example: Wrapping an Existing Function

```python
from cmdi import command, CmdArgs, strip_cmdargs, CmdResult, Pipe
from typing import Unpack

# The original function (untouched)
def foo(x: int) -> int:
    print(f"Given Value: {x}")
    return x * 2

# The wrapper function applies the command interface
@command
def foo_cmd(x: int, **cmdargs: Unpack[CmdArgs]) -> int:
    # Use strip_cmdargs to remove special command arguments before calling the original
    return foo(**strip_cmdargs(locals()))

result = foo_cmd(2, _stdout=Pipe())

assert isinstance(result, CmdResult)  # True
print(result.stdout)  # Given Value: 2
print(result.value)   # 4
```

This approach lets you add powerful command features—such as output redirection, error handling, and status reporting—to any function, without changing its implementation. It's especially useful for integrating third-party or legacy code into a command-driven workflow.

### Command Interface Wrappers for Functions Using `subprocess`

The command interface integrates smoothly with functions that invoke subprocesses, making it easy to capture output, handle errors, and propagate return codes.

#### Example: Wrapping a Subprocess-Calling Function

Suppose you have a function that runs several subprocesses and you want to wrap it with the command interface to capture output and handle errors gracefully:

```python
import subprocess as sp
from cmdi import command, CmdArgs, strip_cmdargs, CmdResult, Pipe
from typing import Unpack

def my_subprocess_calling_func(my_arg: str) -> str:
    print("Running Command 1")
    sp.run(["my_cmd_1", my_arg], check=True)
    # ... do other stuff ...
    print("Running Command 2")
    result = sp.run(["my_cmd_2", my_arg], check=True)
    # ... process result ...
    some_val: str = "done"
    return some_val

@command
def my_subprocess_calling_func_cmd(my_arg: str, **cmdargs: Unpack[CmdArgs]) -> str:
    return my_subprocess_calling_func(**strip_cmdargs(locals()))

result = my_subprocess_calling_func_cmd("my_arg", _stderr=Pipe(text=False))

# If a subprocess fails (e.g., with returncode 32 and error output), you get:
assert isinstance(result, CmdResult)
print(result.code)      # 32
print(result.stderr_b)  # b"Error output"
```

With this pattern, if any subprocess call fails (raises `CalledProcessError`), the command interface will catch it (if `_catch_err=True`) and populate the `CmdResult` with the return code and error output.

#### Advanced: Custom Handling of Subprocess Return Codes

If you need to map specific subprocess return codes to custom statuses or results, you can catch `subprocess.CalledProcessError` in your wrapper and return a tailored `CmdResult`:

```python
import subprocess as sp
from cmdi import command, CmdResult, Status, CmdArgs, strip_cmdargs
from typing import Unpack

def foo(x: str) -> int:
    return sp.run([x], check=True).returncode

@command
def foo_cmd(x: str, **cmdargs: Unpack[CmdArgs]) -> CmdResult:
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
            # Re-raise to let the command interface handle as an error
            raise

```

This lets you flexibly map subprocess exit codes to custom statuses, or handle them however you need, while still benefiting from the command interface's output and error management.


## API

### The `@command` Decorator

The `@command` decorator is the heart of the cmdi library. It wraps your function with a powerful command interface, enabling advanced output management, error handling, and status reporting—all with minimal changes to your code.

A function decorated with `@command` can accept several special keyword arguments that control its runtime behavior:

#### `_verbose: bool = True`

Controls whether command headers and status messages are printed during execution.

**Example:**

```python
result = my_command_func("some_arg", _verbose=False)
```

#### `_color: bool = True`

Enables or disables colored output for command headers and status messages.

**Example:**

```python
result = my_command_func("some_arg", _color=False)
```

#### `_stdout: Optional[Pipe] = None`

Redirects or captures the standard output (stdout) of the decorated function. See the `Pipe` documentation below for configuration options.

**Example:**

```python
from cmdi import Pipe

pipe = Pipe(text=False, tty=True)  # See Pipe docs for all arguments

result = my_command_func('foo', _stdout=pipe)

print(result.stdout)  # Prints the captured output.
```

#### `_stderr: Union[Optional[Pipe], STDOUT] = None`

Redirects or captures the standard error (stderr) of the decorated function. You can also redirect stderr to stdout using `STDOUT`.

**Example:**

```python
from cmdi import Pipe

pipe = Pipe(text=False, tty=True)

result = my_command_func('foo', _stderr=pipe)

print(result.stderr)  # Prints the captured error output.
```

To redirect `stderr` to `stdout`:

```python
from cmdi import STDOUT

result = my_command_func('foo', _stdout=Pipe(), _stderr=STDOUT)
```

#### `_catch_err: bool = True`

Catches exceptions raised by the decorated function and returns error information in the `CmdResult` object, instead of raising the exception. The result will include error details in `result.stderr`, a nonzero `result.code`, and a red status message.

**Example:**

```python
from cmdi import Pipe

r = my_command_func("some_arg", _catch_err=True, _stderr=Pipe())

print(r.status)   # Error
print(r.code)     # 1
print(r.stderr)   # The stderr output from the function call.
```


### class `CmdResult`

The `CmdResult` class is a structured result object returned by any function decorated with `@command`. It provides a consistent interface for accessing the outcome, output, and status of a command.

**Fields:**

- `value: T`  
  The return value of the wrapped function.
- `code: int`  
  The exit or return code (0 for success, nonzero for errors).
- `name: str`  
  The command name (defaults to the function name).
- `status: Optional[Status]`  
  The status of the command (e.g., `ok`, `error`, `skip`).
- `color: Optional[StatusColor]`  
  The color associated with the status (for terminal output).
- `stdout: str`  
  Captured standard output (as text).
- `stderr: str`  
  Captured standard error (as text).
- `stdout_b: bytes`  
  Captured standard output (as bytes, if requested).
- `stderr_b: bytes`  
  Captured standard error (as bytes, if requested).

**Example:**

```python
result = my_command_func("foo")
print(result.value)     # The function's return value
print(result.code)      # 0 if successful, or error code
print(result.stdout)    # Captured stdout as string
print(result.stderr)    # Captured stderr as string
print(result.status)    # Status.ok, Status.error, etc.
print(result.color)     # StatusColor.green, StatusColor.red, etc.
```

You can also construct a `CmdResult` manually if you need to customize the result fields (see "Customizing the Result of a Command Function" above).


### class `Pipe`

The `Pipe` class is used to configure how the standard output (`stdout`) and standard error (`stderr`) streams are handled for a command. By passing a `Pipe` instance to the `_stdout` or `_stderr` keyword arguments, you can flexibly capture, redirect, mute, or process output at a low level—including output from subprocesses or C extensions.

**Fields:**

- `save: bool = True`  
  If `True`, the output is captured and made available in the `CmdResult`. If `False`, output is not saved.
- `text: bool = True`  
  If `True`, output is captured as text (`str`). If `False`, output is captured as bytes (`bytes`).
- `fd: bool = False`  
  If `True`, output is redirected at the file descriptor level (using `os.dup`). This is required to capture output from subprocesses or C code. (Previously called `dup`.)
- `tty: bool = False`  
  If `True`, ANSI color sequences are preserved in the captured output. If `False`, they are stripped.
- `mute: bool = False`  
  If `True`, output is not shown in the terminal during execution (but can still be saved and returned).

**Example:**

```python
from cmdi import CmdResult, Pipe

out_pipe = Pipe(text=False, fd=True, mute=True)
err_pipe = Pipe(text=False, fd=True, mute=False)

result = foo_cmd(10, _stdout=out_pipe, _stderr=err_pipe, _catch_err=True)

print(result.stdout)  # prints captured output
print(result.stderr)  # prints captured error output
```


### Redirecting Output from Subprocesses and External/C Code

When your function runs a subprocess or calls external/foreign/C code, standard Python output redirection may not be enough. To reliably capture all output (including from subprocesses or C extensions), use a `Pipe` with the argument `fd=True`. This enables low-level file descriptor redirection, ensuring that all output is caught.

**Example:**

```python
import subprocess
from cmdi import command, Pipe, CmdResult

@command
def foo(x, **cmdargs) -> CmdResult:
    subprocess.run("my_script")

# Capture stdout from the function (including subprocess output) via low-level redirect:
foo(_stdout=Pipe(fd=True))
```

This approach ensures that even output written directly to the OS-level file descriptors (such as from subprocesses or C libraries) is captured and made available in the `CmdResult`.

### function `strip_cmdargs(locals_)`

Removes special command interface arguments (such as `_stdout`, `_stderr`, `_catch_err`, etc.) from a dictionary, typically `locals()`. This is useful when writing command wrappers that need to forward only the original function arguments, excluding cmdi-specific ones.

**Parameters:**

- `locals_ : Dict[str, Any]`  
  The dictionary of local variables, usually from `locals()` inside a wrapper function.

**Returns:**

- `Dict[str, Any]`  
  A new dictionary with all command interface arguments removed.

**Example:**

```python
def foo(x):
    # Do a lot of stuff
    return x * 2

@command
def foo_cmd(x, **cmdargs):
    # Remove cmdi-specific arguments before calling the original function
    return foo(**strip_cmdargs(locals()))
```

### function `print_title(result, color=True, file=None)`

Prints a formatted title/header for a command result, typically showing the command name and a separator. This is useful for visually distinguishing command output in logs or the terminal.

**Parameters:**

- `result: CmdResult`  
  The command result object whose name will be displayed as the title.
- `color: bool = True`  
  Whether to use colored output for the title (default: `True`).
- `file: Optional[IO[str]] = None`  
  The file-like object to print to (default: `sys.stdout`).

**Returns:**  
None

**Example:**

```python
result = my_cmd('foo')
print_title(result)
```

**Output:**
```
Cmd: my_cmd
-----------
```


### function `print_status(result, color=True, file=None)`

Prints the status line for a command result, typically showing the command name and its status (such as "Ok", "Error", etc.), optionally with color. This is useful for quickly seeing the outcome of a command in logs or terminal output.

**Parameters:**

- `result: CmdResult`  
  The command result object whose status will be displayed.
- `color: bool = True`  
  Whether to use colored output for the status line (default: `True`).
- `file: Optional[IO[str]] = None`  
  The file-like object to print to (default: `sys.stdout`).

**Returns:**  
None

**Example:**

```python
result = my_cmd('foo')
print_status(result)
```

**Output:**
```
my_cmd: Ok
```


### function `print_result(result, color=True, file=None)`

Prints a full, formatted summary of a `CmdResult` object, including the command title, captured stdout and stderr, and the final status line. This is useful for displaying all relevant output and status information for a command in a clear, readable format.

**Parameters:**

- `result: CmdResult`  
  The command result object to display.
- `color: bool = True`  
  Whether to use colored output for the result (default: `True`).
- `file: Optional[IO[str]] = None`  
  The file-like object to print to (default: `sys.stdout`).

**Returns:**  
None

**Example:**

```python
result = my_cmd('foo')
print_result(result)
```

**Output:**
```
Cmd: my_cmd
-----------
Stdout:
Runtime output of my_cmd...
Stderr:
Some err
my_cmd: Ok
```


### function `print_summary(results, color=True, headline=True, file=None)`

Prints a concise summary of one or more `CmdResult` objects, including command titles, captured output, and status lines for each command. This is especially useful for displaying the results of multiple commands in a readable, organized format.

**Parameters:**

- `results: Union[Optional[CmdResult], List[Optional[CmdResult]]]`  
  A single `CmdResult` or a list of `CmdResult` objects to summarize.
- `color: bool = True`  
  Whether to use colored output for the summary (default: `True`).
- `headline: bool = True`  
  Whether to print a headline/title for each command (default: `True`).
- `file: Optional[IO[str]] = None`  
  The file-like object to print to (default: `sys.stdout`).

**Returns:**  
None

**Example:**

```python
from cmdi import print_summary

results = [
    my_foo_cmd(),
    my_bar_cmd(),
    my_baz_cmd(),
]

print_summary(results)
```

**Output:**
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


### function `read_popen_pipes(p, interval=10)`

Provides a real-time iterator over the output of a running `subprocess.Popen` process, yielding lines from both `stdout` and `stderr` as they become available. This is useful for live monitoring or logging of subprocess output, especially when you want to process both streams in parallel.

**Parameters:**

- `p: subprocess.Popen`  
  The running subprocess whose output you want to read.
- `interval: int = 10`  
  The polling interval (in milliseconds) for reading output streams.

**Returns:**  
`Iterator[Tuple[str, str]]`  
Yields a tuple `(stdout_line, stderr_line)` for each line read from the process's output streams. If only one stream has new output, the other will be an empty string.

**Example:**

```python
from cmdi import POPEN_DEFAULTS, read_popen_pipes
import subprocess

p = subprocess.Popen(mycmd, **POPEN_DEFAULTS)

for out_line, err_line in read_popen_pipes(p):
    if out_line:
        print(out_line, end='')
    if err_line:
        print(err_line, end='')

code = p.poll()
```

This allows you to process or display output from both `stdout` and `stderr` in real time, making it ideal for interactive command-line tools or live logging scenarios.


## Development & Testing

To contribute to `cmdi` or run its test suite, clone the repository and use the following commands.

### Running Tests

The test suite uses `pytest` and is configured to show all output in real time (no output capture). Some tests are visual and require human inspection of the output.

```sh
poetry run pytest --capture=no tests
```

- Make sure you have all development dependencies installed (see `pyproject.toml`).
- Some tests are designed for manual/visual verification—check the output in your terminal.
