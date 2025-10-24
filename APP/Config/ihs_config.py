from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from tkinter import messagebox
from selenium import webdriver
from dotenv import load_dotenv
from pathlib import Path as P
import threading
import oracledb
import os

load_dotenv()

user_oracle = os.getenv('USER_ORACLE')
password = os.getenv('PASSWORD_ORACLE')
dsn = os.getenv('DSN')


def config_webdriver_chrome(automacao):
    """
    Configura e inicializa o WebDriver do Chrome.

    Parâmetros:
        None

    Retorno:
        tuple:
            driver (webdriver.Chrome): Instância do navegador Chrome.
            wdw (WebDriverWait): Objeto para gerenciar esperas explícitas (timeout de 180s).
    """
    try:
        match automacao:
            case 'CNH - Baixas':
                PASTA_DOWNLOADS = P(r"\\172.17.67.14\findev$\Automação - CNH\Baixa de Arquivos\Arquivos Baixados").resolve()
            case 'CNH - Preparação':
                PASTA_DOWNLOADS = P(r"\\172.17.67.14\findev$\Automação - CNH\Preparação das Baixas").resolve()
            case 'CDC':
                PASTA_DOWNLOADS = P(r"\\172.17.67.14\findev$\Automação - CDC").resolve()
            case _:
                PASTA_DOWNLOADS = P(r"\\172.17.67.14\findev$").resolve()

        
        PASTA_DOWNLOADS.mkdir(parents=True, exist_ok=True)
        
        service = ChromeService(ChromeDriverManager().install())

        options = ChromeOptions()
        options.add_experimental_option("prefs", {
            "download.default_directory": str(PASTA_DOWNLOADS),
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        
        driver = webdriver.Chrome(service=service, options=options)
        
        wdw = WebDriverWait(driver, 180)
        
        driver.maximize_window()
        
        configurar_extensao(driver)
        
        return (driver, wdw, PASTA_DOWNLOADS)
    except Exception:
        driver.close()


def configurar_extensao(driver):
    url = 'https://chromewebstore.google.com/detail/rektcaptcha-recaptcha-sol/bbdhfoclddncoaomddgkaaphcnddbpdh?hl=pt-BR&utm_source=ext_sidebar'
    driver.get(url)
    
    resposta = messagebox.askyesno(title='Extensão', message='Você já adicionou a extensão?')
    while not resposta:
        resposta = messagebox.askyesno(title='Extensão', message='Você precisa adicionar a extensão, já fez?')

wdw = None
PASTA_DOWNLOADS = None
_driver = None
_lock = threading.Lock()

def _ensure_driver(automacao):
    """Garante que o driver global exista e esteja válido."""
    global wdw
    global PASTA_DOWNLOADS
    global _driver
    global _lock
    
    with _lock:
        if _driver is None:
            _driver, wdw, PASTA_DOWNLOADS = config_webdriver_chrome(automacao)
        else:
            # Verifica se ainda está vivo
            try:
                _driver.title  # chamada simples para validar sessão
            except WebDriverException:
                _driver, wdw, PASTA_DOWNLOADS = config_webdriver_chrome()
    return (_driver, wdw, PASTA_DOWNLOADS)

def connection():
    """
    Cria uma conexão com o banco de dados Oracle.

    Parâmetros:
        None

    Retorno:
        oracledb.Connection: Objeto de conexão ativo com o banco de dados Oracle.
    """
    oracledb.init_oracle_client(
        lib_dir=r'C:\instantclient'
    )

    # Conexão com o Oracle
    return oracledb.connect(
        user=user_oracle,
        password=password,
        dsn=dsn
    )


def busca_dados_db():
    """
    Busca dados financeiros no banco de dados Oracle.

    Executa uma query que retorna informações de títulos e clientes
    com status 'EM', tipo 'CR', empresa = 2 e origem = 1252.

    Parâmetros:
        None

    Retorno:
        list[tuple]: Lista de tuplas contendo os resultados da query:
            (revenda, título, duplicata, valor_título, status, cliente, nome_cliente).
    """
    conn = connection()

    try:
        cur = conn.cursor()

        cur.execute(
            f'''SELECT
            A.REVENDA, A.TITULO, A.DUPLICATA, A.VAL_TITULO, A.DEPARTAMENTO, A.STATUS, A.CLIENTE, A.EMPRESA, B.NOME
        FROM
            FIN_TITULO  A
        JOIN FAT_CLIENTE  B ON B.CLIENTE = A.CLIENTE 
        WHERE
            A.STATUS = 'EM'
            AND A.TIPO = 'CR'
            AND A.ORIGEM = 1252'''  # Origem = Venda com Financiamento
        )

        return cur.fetchall()
    finally:
        cur.close()
        conn.close()