from setuptools import setup, find_packages

setup(
    name='python_logger_package',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'os',  # Example of a dependency
        'sys',  # Example of a versioned dependency
        'datetime',
        'smtplib',
        'sqlalchemy',
        'dotenv',
        'traceback',
        'warnings',
        'email.mime.application','email.mime.multipart','email.mime.text'
    ],
        #install_requires=['os','sys','pandas','datetime','smtplib','email.mime.application','email.mime.multipart','email.mime.text','sqlalchemy','dotenv','traceback,warnings',], # add any additional packages that 

)
