# Package Description

This package provides a simple logging decorator for Python jobs, to insert rows to an SQL table on both success and failure.

## Installation

You can install the package using pip:

```bash
pip install pyesrlogger
```
or via

```bash
python -m pip install git+https://github.com/khainesesr/pyesrlogger.git
```

## How to use

```Python
import sys
from pyesrlogger import JobHandler
from datetime import datetime



current_date = datetime.today().strftime('%Y-%m-%d')
error_handler = JobHandler(message=f"Job completed successfuly. Updated data as at {current_date}")



@error_handler
def main():
   print(7 / 2)  # Perform division
   return 0



print(__name__)
if __name__ == '__main__':
   main()
```
