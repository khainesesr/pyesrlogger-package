"""Decorator function for encapsulating capacity to log job in SQL table on completion 
and send email/log error upon error/exception"""

import os
import sys
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy import create_engine
import dotenv
import traceback
import warnings
from envdecorator import load_env_from_dir
from pathlib import Path

class JobHandler:
    def __init__(self,message='Job completed successfully',email_recipients='',server='', env_path=''):
        curr_dir = str(os.getcwd())
        env_string = ",".join([curr_dir, env_path])
        load_env_from_dir(env_string)
        self.message = 'Job completed successfully' if not message else message #use default message for jobs finish successfully.
        self.user = os.getlogin()
        if self.user == 'sys_informatics':
            self.uid = os.environ["sms_uat_uid"]
            self.pwd = os.environ["sms_uat_pass"]
            self.database = os.environ["sm_uat_database"]
            self.server = os.environ["sms_uat_server"]
            self.odbc_driver = os.environ["sql_driver"]
            if 'sms_uat_uid' not in os.environ:
                raise KeyError(f"Environment variable 'uid' not found.")
            if 'sms_uat_pass' not in os.environ:
                raise KeyError(f"Environment variable 'pwd' not found.")
            if 'sm_uat_database' not in os.environ:
                raise KeyError(f"Environment variable 'database' not found.")
            if 'sms_uat_server' not in os.environ:
                raise KeyError(f"Environment variable 'server' not found.")
        #Return working directory for source file that calls this decorator
        source_path = Path(__file__)
        current_path = os.path.abspath(__file__)
        self.error_log = os.path.basename(os.path.dirname(current_path)) + '/log.txt'
        self.status = 'Completed'
        #Use os.environ.get to avoid key error here
        self.email_recipient = email_recipients if email_recipients else os.environ["error_email"] if os.environ.get("error_email") else ''

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                return 'Success',func(*args, **kwargs)
            except Exception as e:
                return e,sys.exc_info()
        error,stack = wrapper()
        #The wrapper function encounted an Exception
        if isinstance(error, Exception):
            traceback_info = traceback.extract_tb(stack[2])
            if traceback_info:
                nl = '\n'
                print(f"{str(error)} exception. {nl} Filename {traceback_info[-1].filename}, line number {traceback_info[-1].lineno}, at {traceback_info[-1].line}")
                self.status = 'Error'
                df = self.write_error(self.status,error,self.email_recipient,traceback_info,self.error_log,self.user)
                #Only insert row when user is sys_informatics
                if self.user == 'sys_informatics':
                    self.database_load(df,self.uid,self.pwd,self.database,self.server,self.odbc_driver,error,self.error_log)
        #No exception encountered. Continue as script has completed successfully
        elif stack is None:
            df = self.write_error(self.status,self.message,self.email_recipient,'',self.error_log,self.user)
            #Only insert row when user is sys_informatics
            if self.user == 'sys_informatics':
                self.database_load(df,self.uid,self.pwd,self.database,self.server,self.odbc_driver,self.message,self.error_log)
        return wrapper

    def find_filename(self,status):
        "Return filename soure of error"
        return os.path.abspath(sys.argv[0])

    def send_email(self,df,status,error,email,output_file,path):
            """Send email on error, with various parameters"""
            if status == 'Error' and email and email != None :
                try:
                    #Setup email defaults
                    msg = MIMEMultipart()
                    msg['Subject'] = f'sys_informatics error - {path}'
                    msg['From'] = "sysinformatics@esr.cri.nz"
                    #Split email string into list and then convert back to string for encode
                    msg['To'] = ", ".join(email.split(","))
                    lines = [f"{column}:" + "\n".join(df[column].astype(str).tolist()) + "\n" \
                        for column in df.columns]
                    #Prep email message contents
                    lines = lines + \
                        [f'Please refer to log file under {output_file} for additional error info']
                    msg.attach(MIMEText("\n".join(lines), 'plain'))
                    # Send email
                    s = smtplib.SMTP('mail.esr.cri.nz')
                    s.send_message(msg)
                    s.quit()
                except Exception as e:
                    warnings.warn(e)
            else:
                if status != 'Error':
                    print('Job completed successfully, no email sent.')
                if status == 'Error' and not email:
                    warnings.warn('No email addresses found, no email sent')

    def write_error(self,status,message,email,stack,output_file,user):
            """Generate and format dataframe presented in error email"""
            #Set error_message as only custom message on successful complete
            if message and status == 'Completed':
                error_message = message
            #Set error_message as error message and error details
            elif message and stack:
                nl = '\n'
                error_message = f'{str(message)} exception. {nl} Filename {stack[-1].filename}, line number {stack[-1].lineno}, at {stack[-1].line}'
            path = ""
            path = self.find_filename(status)
            if not path:
                path = 'Cannot determine path'
                warnings.warn(path)
            time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            df = pd.DataFrame({
                "Status": [status],
                "path": [path],
                "user": [user],
                "time": [time],
                "errormessage": [error_message],
            })
            try:
                self.send_email(df,status,message,email,output_file,path)
            except Exception as e:
                warnings.warn(e)
                warnings.warn("Cannot send email")
            return df

    def database_load(self,df,uid,pwd,db,server,driver,message,output_file):
        """Insert job run details to database"""
        #Remove unnecessary text included in email to database.
        #Only insert string representation of error, or custom message
        df['errormessage'] = str(message)
        if uid and pwd and db and server:
            try:
                connection_string = f"mssql+pyodbc://{uid}:{pwd}@{server}/{db}?driver={driver}&ApplicationIntent=ReadOnly"
                engine = create_engine(connection_string, echo=False) # Set echo to True to see SQL queries in the console
                with engine.connect() as error_con:
                    df.to_sql('ErrorLogger', con=error_con, if_exists='append', index=False)
                    print('row inserted successfully')
            except Exception as e:
                warnings.warn(e)
        else:
            warnings.warn("Credentials not all supplied for connection string. Please check all credentials are supplied in env file")
