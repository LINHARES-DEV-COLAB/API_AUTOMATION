# APP/Services/teste_selenium.py
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class SeleniumTest:
    def __init__(self):
        chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/chromium")
        chromedriver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

        # Valida existência (ou no PATH) antes de tentar iniciar
        if not (os.path.exists(chrome_bin) or shutil.which(os.path.basename(chrome_bin))):
            raise RuntimeError(
                f"Chromium/Chrome não encontrado. Defina CHROME_BIN ou instale o navegador. "
                f"Tentado: {chrome_bin}"
            )
        if not (os.path.exists(chromedriver_path) or shutil.which(os.path.basename(chromedriver_path))):
            raise RuntimeError(
                f"Chromedriver não encontrado. Defina CHROMEDRIVER_PATH ou instale o driver. "
                f"Tentado: {chromedriver_path}"
            )

        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-software-rasterizer")
        opts.add_argument("--window-size=1920,1080")
        opts.binary_location = chrome_bin

        try:
            service = Service(executable_path=chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=opts)
        except Exception as e:
            raise RuntimeError(f"Falha ao iniciar WebDriver: {e}") from e

    def get(self, url: str):
        self.driver.get(url)
        return self.driver.title

    def quit(self):
        try:
            self.driver.quit()
        except Exception:
            pass
