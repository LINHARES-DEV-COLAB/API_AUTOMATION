from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from tkinter import messagebox
from pathlib import Path as P
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, NoSuchElementException


def config_webdriver_chrome():
    """
    Configura e inicializa o WebDriver do Chrome.

    Parâmetros:
        None

    Retorno:
        tuple:
            driver (webdriver.Chrome): Instância do navegador Chrome.
            wdw (WebDriverWait): Objeto para gerenciar esperas explícitas (timeout de 180s).
    """
    global driver
    try:
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

def _ensure_driver(_driver, _lock):
    """Garante que o driver global exista e esteja válido."""
    with _lock:
        if _driver is None:
            _driver, wdw, PASTA_DOWNLOADS = config_webdriver_chrome()
        else:
            # Verifica se ainda está vivo
            try:
                _driver.title  # chamada simples para validar sessão
            except WebDriverException:
                _driver, wdw, PASTA_DOWNLOADS = config_webdriver_chrome()
    return (_driver, wdw, PASTA_DOWNLOADS)