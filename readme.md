# My Decorator Package

This package provides a simple logging decorator for Python jobs, on both success and failure.

## Installation

You can install the package using pip:

```bash
pip install PythonErrorLogging
```
or via

```bash
python -m pip install git+https://github.com/khainesesr/pyesrlogger.git
```

## How to use

```Python
from pyesrlogger import JobHandler

error_handler = JobHandler(message="testing completed error message")

@error_handler
def example_func():
  return .
```
