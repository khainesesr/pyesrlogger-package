# Package Description

This package provides a simple logging decorator for Python jobs, to insert rows to an SQL table on both success and failure.

## Installation

Before installing this package, please run
```Python
pip install --upgrade pip setuptools wheel
```

You can install the package using pip install via github

```bash
python -m pip install git+https://github.com/khainesesr/pyesrlogger.git
```

if there is a pyodbc related error during install, please run the below command

```Python
python -m pip install pyodbc
```

## Parameters
message - optional. Message to insert to database on successful completion. Defaults to text 'job completed successfully'  
email_recipient - optional. Defaults to error_email defined on sys_informatics environ, otherwise uses this parameter. Must be string, with email addresses separated by commas eg "email1@esr.cri.nz, email2@esr.cri.nz"  
env_path - optional. If defining variables in directory other than top level .Renviron, pass directory path

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
