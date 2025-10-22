import os
from pathlib import Path

class Config:
    # Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "Data"
    UPLOAD_DIR = DATA_DIR / "uploads"
    RESULTS_DIR = DATA_DIR / "results"
    TEMP_DIR = DATA_DIR / "temp"
    
    # Rede PAN
    PAN_NETWORK_PATH = r"\\172.17.67.14\Ares Motos\controladoria\financeiro\06.CONTAS A RECEBER\11.RELATÓRIOS BANCO PAN"
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    
    def create_directories(self):
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)

config = Config()
config.create_directories()