from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from tkinter import messagebox
from selenium import webdriver
from dotenv import load_dotenv
from pathlib import Path as P
from time import sleep
import threading
import pyautogui
import oracledb
import os

load_dotenv()

user_oracle = os.getenv('USER_ORACLE')
password = os.getenv('PASSWORD_ORACLE')
dsn = os.getenv('DSN')


def config_webdriver_chrome(PASTA_DOWNLOADS):
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
        PASTA_DOWNLOADS = P(PASTA_DOWNLOADS).resolve()
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

    pyautogui.PAUSE = 3
    
    # driver.execute_script("document.body.style.zoom='75%'")

    pyautogui.click(1520, 364)  # Clicar em adicionar a extensão ao Chrome
    # pyautogui.click(1167, 256)  # Clicar em adicionar a extensão ao Chrome

    pyautogui.click(1002, 300)  # Clica para configurar a extensão

    sleep(6)
    pyautogui.click(1777, 78)  # Clica para configurar a extensão
    pyautogui.click(1534, 275)
    pyautogui.click(1679, 223)
    pyautogui.click(1683, 335)
    pyautogui.click(1674, 513, clicks=2, duration=1)
    pyautogui.write('2000')
    pyautogui.click(1071, 517)
    # pyautogui.click(1596, 61)  # Clica para configurar a extensão
    # pyautogui.click(1596, 61)  # Clica para configurar a extensão
    # pyautogui.click(1408, 219)
    # pyautogui.click(1513, 180)
    # pyautogui.click(1514, 268)
    # pyautogui.click(1510, 411, clicks=2, duration=1)
    # pyautogui.write('2000')
    # pyautogui.click(1073, 385)

wdw = None
PASTA_DOWNLOADS = None
_driver = None
_lock = threading.Lock()

def _ensure_driver(pasta_downlod=r"\\172.17.67.14\findev$\Automação - CNH\Baixa de Arquivos\Arquivos Baixados"):
    """Garante que o driver global exista e esteja válido."""
    global wdw
    global PASTA_DOWNLOADS
    global _driver
    global _lock
    
    with _lock:
        if _driver is None:
            _driver, wdw, PASTA_DOWNLOADS = config_webdriver_chrome(pasta_downlod)
        else:
            # Verifica se ainda está vivo
            try:
                _driver.title  # chamada simples para validar sessão
            except WebDriverException:
                _driver, wdw, PASTA_DOWNLOADS = config_webdriver_chrome(pasta_downlod)
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