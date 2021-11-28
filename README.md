# IO Check

Is a tool for simple checking the executable standard IO (output, error output).

## Getting started

Download a [``iocheck.py``](./iocheck.py) file from this repository:

```shell
cd <TO YOUR DIRECTORY>
wget  https://raw.githubusercontent.com/pestanko/iocheck/master/iocheck.py
```

Take a look at [examples](./examples) how to develop a tests for your executable.

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
