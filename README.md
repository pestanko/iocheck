# IO Check

Is a tool for simple checking the executable standard IO (output, error output).

## Getting started

Download a [``iocheck.py``](./iocheck.py) file from this repository:

```shell
cd <TO YOUR DIRECTORY>
wget  https://raw.githubusercontent.com/pestanko/iocheck/master/iocheck.py
```

Take a look at [examples](./examples) how to develop a tests for your executable.

## Tests structure

The ``iocheck`` tests are simple comparison of expected `stdout`, `stderr` and return/exit code with the ones,
generated by executable run.

The tests by default can be stored in one of the three directories: ``./iotest``, `./io_test` or ``./tests``.
This can be "overridden" by explicitly specifying the tests' directory location by ``-T`` (see `--help`).

### How to write a test

Files that belong to one test, has the same file name without the extension,
the extension is defining how the file should be used.

For Example, lets have test `test_echo`, you can have these files:
- `test_echo.arg` - defines what arguments will be provided to the binary (separated by a new line), (if not provided, empty)
- `test_echo.in` - defines what will be provided on `stdin` (if not provided, empty)
- `test_echo.out` - defines expected `stdout` (if not provided, it is expected to be any)
- `test_echo.err` - defines expected `stderr` (if not provided, it is expected to be any)
- `test_echo.exit` - defines what exit code is expected (if not provided, zero (0), is expected)

The tests' directory can contain multiple subdirectories (these can contain subtests),
this is allowed in order to better structure/group your tests.


## Example usage

If you want to follow the example [echocat](./examples/echocat) you can do the following

```shell
# Clone the repository
git clone https://github.com/pestanko/iocheck.git
# Go to the cloned repository
cd iocheck
# Build the echocat example
cmake -B examples/echocat/build -S examples/echocat/
cmake --build examples/echocat/build
# execute the tests
python -m iocheck -T examples/echocat/io_tests examples/echocat/build/echocat
```

The usage of `iocheck` script is the following:

- ``python -m iocheck`` - call the module using the Python
- ``-T/--tests`` - specify the location of the `tests` directory
  - Note: this is not necessary if your tests are stored in one of the following directories:``./iotests``, `./io_tests`, `./tests`
- Positional parameter ``examples/echocat/build/echocat`` is the location of the executable


## Configuration

The verbosity of logging can be set by setting the ``LOG_LEVEL`` environment variable or providing `-L/--log-level`
