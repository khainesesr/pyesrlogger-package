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
Renvconfigfile='../.Renviron'
dotenv.load_dotenv(Renvconfigfile)
from decorators import load_env_files_from_dir

@load_env_files_from_dir('env_path')
class JobHandler:
    def __init__(self,message='job completed successfully',email_recipient='',uid='',
    pwd='',database='',server='', env_path=''):
        #pass
        self.env_path = env_path  # Set the directory for env files
        self.message = 'job completed successfully' if not message else message
        self.uid = os.environ["sms_uat_uid"]
        self.pwd = os.environ["sms_uat_pass"]
        self.database = os.environ["sm_uat_database"]
        self.server = os.environ["sms_uat_server"]
        self.odbc_driver = os.environ["sql_driver"]
        if 'uid' not in os.environ:
            raise KeyError(f"Environment variable 'MY_ENV_VAR' not found.")
        if 'pwd' not in os.environ:
            raise KeyError(f"Environment variable 'MY_ENV_VAR' not found.")
        if 'database' not in os.environ:
            raise KeyError(f"Environment variable 'MY_ENV_VAR' not found.")
        if 'server' not in os.environ:
            raise KeyError(f"Environment variable 'MY_ENV_VAR' not found.")
        #self.email_recipient = os.environ["error_email"] if error else '' #PROD deployment
        self.error_log = os.path.dirname(os.path.realpath(__file__)) + '/log.txt'
        self.error = sys.exc_info()[0] #error
        self.status = 'Completed'
        self.email_recipient = ''
        self.custom = ''#custom_msg

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                return 'Success',func(*args, **kwargs)
            except Exception as e:
                return e,sys.exc_info()  # Or handle the error as needed
        error,stack = wrapper()
        print(stack)
        #The wrapper function encounted an Exception
        if isinstance(error, Exception):
            self.status = 'Error'
            self.email_recipient = 'kaitlin.haines@esr.cri.nz'
            df = self.write_error(self.status,error,self.email_recipient,stack,self.error_log)
            self.database_load(df,self.uid,self.pwd,self.database,self.server,self.odbc_driver,error,self.error_log)
        #No exception encountered
        elif stack is None:
            df = self.write_error(self.status,self.message,self.email_recipient,'',self.error_log)
            self.database_load(df,self.uid,self.pwd,self.database,self.server,self.odbc_driver,self.message,self.error_log)
        return wrapper

    def handle_error(self, error):
        # Default error handling behavior
        print(f"An error occurred: {error}")
        
    def find_filename(self,status):
        "Return filename soure of error"
        print(os.path.abspath(sys.argv[0]))
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
                    log_dir = os.path.dirname(os.path.realpath(__file__))
                    #Prep email message contents
                    lines = lines + \
                        [f'Please refer to log file under {log_dir} for additional error info']
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

    def write_error(self,status,message,email,stack,output_file):
            nl = '\n'
            #Set error_message as only custom message on successful complete
            if message and status == 'Completed':
                error_message = message
            #Set error_message as both custom message and error message
            elif message and stack:
                error_message = f'{str(stack[0])}. Source: line {stack[2].tb_lineno}.'
            path = ""
            path = self.find_filename(status)
            if not path:
                print(path)
                path = 'Cannot determine path'
                with open(output_file, "a") as file:
                    file.write('Cannot determine path')
            user = os.getenv("USER")
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

