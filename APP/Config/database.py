 # Conexão Oracleimport os
import oracledb
from dotenv import load_dotenv
import os

load_dotenv()

class DatabaseConfig:
    def __init__(self):
        self.user = os.getenv('USER_ORACLE_original')
        self.password = os.getenv('PASSWORD_ORACLE_original')
        self.dsn = os.getenv('DSN')
    
    def get_connection(self):
        oracledb.init_oracle_client(lib_dir=r'C:\instantclient')
        return oracledb.connect(
            user=self.user,
            password=self.password,
            dsn=self.dsn
        )