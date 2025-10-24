import os
from dotenv import load_dotenv
import oracledb

load_dotenv()

class Config:
    # Configurações Oracle
    USER_ORACLE = os.getenv('USER_ORACLE')
    PASSWORD_ORACLE = os.getenv('PASSWORD_ORACLE')
    DSN = os.getenv('DSN')
    
    # Diretório de rede base para os relatórios PAN
    BASE_DIR_REDE = r"\\172.17.67.14\Ares Motos\controladoria\financeiro\06.CONTAS A RECEBER\11.RELATÓRIOS BANCO PAN"
    
    # Configurações da aplicação
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

def get_oracle_connection():
    """Estabelece conexão com o Oracle"""
    try:
        oracledb.init_oracle_client(lib_dir=r'C:\instantclient')
    except:
        pass  # Client já inicializado
    
    return oracledb.connect(
        user=Config.USER_ORACLE,
        password=Config.PASSWORD_ORACLE,
        dsn=Config.DSN
    )