# Package Description

This package provides a simple logging decorator for Python jobs. When deployed on sys_informatics account, this decorator will insert rows to an SQL table on both success and failure, and send an email on failure to specified individuals. Testing locally on windows will only return a string representation of the error in the python terminal.

## Installation

Before installing this package, please run
```Python
pip install --upgrade pip setuptools wheel
```

You can install the package using pip install via github

```bash
python -m pip install git+https://github.com/khainesesr/pyesrlogger.git
```

if there is a pyodbc or 'envdecorator' related error during install, please run the below commands

```Python
python -m pip install pyodbc
pip install git+https://github.com/khainesesr/envdecorator-package.git
```

## Parameters
message - optional. Message to insert to database on successful completion. Defaults to text 'job completed successfully'.  
email_recipient - optional. Defaults to error_email defined on sys_informatics environ, otherwise uses this parameter. Must be string, with email addresses separated by commas eg "email1@esr.cri.nz, email2@esr.cri.nz".  
env_path - optional. Must be string, with directory paths separated by commas, as in email_recipient parameter. Use to pass env files contained in a directory other than top level .Renviron. Any Python env file passed must contain 'env' in the name. Any R env file should follow standard Renviron naming behaviour.

## How to use
This decorator is intended to be used in conjunction with a main() function. Any exceptions returned by sub-functions or caught in the main() function will be captured.
The JobHandler() class automatically loads any .env or .Renviron from the current working directory. To load from another directory, please specify using decorator

```Python
import sys
import importlib
from pyesrlogger import JobHandler
from envdecorator import load_env_from_dir
import os

#Directory with custom env files
dir_name = 'path/to/dir'
error_handler = JobHandler(message="testing completed error message",email_recipients='kaitlin.haines@esr.cri.nz',env_path=dir_name)

def test_subfunc():
        return 7/0

@error_handler
def main():
    zero_div = test_subfunc()  # Perform division
    return zero_div

print(__name__)
if __name__ == '__main__':
    main()
```
