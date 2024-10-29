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

curr = str(os.getcwd())
@load_env_from_dir(curr)
class JobHandler:
    def __init__(self,message='job completed successfully',email_recipients='',uid='',
    pwd='',database='',server='', env_path=''):
        #pass
        self.env_path = env_path  # Set the directory for env files
        self.message = 'job completed successfully' if not message else message
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
        #self.email_recipient = os.environ["error_email"] if error else '' #PROD deployment
        source_path = Path(__file__)
        #print(source_path.parent)
        #print(source_path.absolute())
        current_path = os.path.abspath(__file__)
        self.error_log = os.path.basename(os.path.dirname(current_path)) + '/log.txt'
        #self.error_log = os.path.basename(os.path.dirname(source_path)) + '/log.txt'
        #self.error_log = str(source_path.parent.absolute()) + '/log.txt'
        #print(self.error_log)
        self.error = sys.exc_info()[0] #error
        self.status = 'Completed'
        self.email_recipient = email_recipients if email_recipients else ''
        self.custom = ''#custom_msg

    def get_traceback(self):
        #source_path = Path(__file__)
        #self.error_log = source_path.parent.absolute()
        #self.error_log = os.path.basename(os.path.dirname(source_path)) + '/log.txt'
        return traceback.extract_stack()

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                return 'Success',func(*args, **kwargs)
            except Exception as e:
                return e,sys.exc_info()  # Or handle the error as needed
        error,stack = wrapper()
        #The wrapper function encounted an Exception
        if isinstance(error, Exception):
            traceback_info = self.get_traceback()
            if traceback_info:
                print(f"{str(error)} exception occurred in file: {traceback_info[0].filename}, line: {traceback_info[0].lineno}")
                self.status = 'Error'
                df = self.write_error(self.status,error,self.email_recipient,traceback_info,self.error_log,self.user)
                if self.user == 'sys_informatics':
                    self.database_load(df,self.uid,self.pwd,self.database,self.server,self.odbc_driver,error,self.error_log)
        #No exception encountered
        elif stack is None:
            df = self.write_error(self.status,self.message,self.email_recipient,'',self.error_log,self.user)
            if self.user == 'sys_informatics':
                self.database_load(df,self.uid,self.pwd,self.database,self.server,self.odbc_driver,self.message,self.error_log)
        return wrapper

    def handle_error(self, error):
        # Default error handling behavior
        print(f"An error occurred: {error}")

    def find_filename(self,status):
        "Return filename soure of error"
        #print(os.path.abspath(sys.argv[0]))
        return os.path.abspath(sys.argv[0])

    def send_email(self,df,status,error,email,output_file,path):
            """Send email on error, with various parameters"""
            if status == 'Error' and email and email != None :  #and email.strip()
                try:
                    msg = MIMEMultipart() #MIMEMultipart('alternative')
                    msg['Subject'] = f'sys_informatics error - {path}'
                    msg['From'] = "sysinformatics@esr.cri.nz"
                    #Split email string into list and then convert back to string for encode
                    msg['To'] = ", ".join(email.split(","))
                    lines = [f"{column}:" + "\n".join(df[column].astype(str).tolist()) + "\n" \
                        for column in df.columns]
                    #log_dir = os.path.dirname(os.path.realpath(__file__))
                    #Prep email message contents
                    lines = lines + \
                        [f'Please refer to log file under {output_file} for additional error info']
                    msg.attach(MIMEText("\n".join(lines), 'plain'))
                    # Send the email
                    s = smtplib.SMTP('mail.esr.cri.nz')
                    s.send_message(msg)
                    s.quit()
                except Exception as e:
                    print(e)
                    with open(output_file, "a") as file:
                        file.write(str(e))
                    pass
            else:
                if status != 'Error':
                    with open(output_file, "a") as file:
                        file.write('Job completed successfully, no email sent.')
                    print('Job completed successfully, no email sent.')
                if status == 'Error' and not email:
                    with open(output_file, "a") as file:
                        file.write('No email addresses found, no email sent')
                    warnings.warn('No email addresses found, no email sent')

    def write_error(self,status,message,email,stack,output_file,user):
            nl = '\n'
            #Set error_message as only custom message on successful complete
            if message and status == 'Completed':
                error_message = message
            #Set error_message as both custom message and error message
            elif message and stack:
                error_message = f'{str(message)}. Source: line {stack[0].lineno}.'
                #error_message = 'test'
            path = ""
            path = self.find_filename(status)
            if not path:
                path = 'Cannot determine path'
                with open(output_file, "a") as file:
                    file.write('Cannot determine path')
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
                print(str(e))
                warnings.warn(e)
                warnings.warn("Cannot send email")
                with open(output_file, "a") as file:
                    file.write('Cannot send email')
            return df

    def database_load(self,df,uid,pwd,db,server,driver,message,output_file):
        """Insert job run details to database"""
        #Remove unnecessary text included in email to database.
        #Only insert error or custom message
        df['errormessage'] = str(message)
        if uid and pwd and db and server:
            try:
                connection_string = f"mssql+pyodbc://{uid}:{pwd}@{server}/{db}?driver={driver}&ApplicationIntent=ReadOnly"
                engine = create_engine(connection_string, echo=False) # Set echo to True to see SQL queries in the console
                with engine.connect() as error_con:
                    df.to_sql('ErrorLogger', con=error_con, if_exists='append', index=False)
                    print('row uploaded successfully')
            except Exception as e:
                #with open(output_file, "a") as file:
                #   file.write(str(e))
                print(e)
                warnings.warn(e)
                pass
        else:
            warnings.warn("Credentials not all supplied for connection string. Please check all credentials supplied in env file")
