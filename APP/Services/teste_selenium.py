# APP/Services/teste_selenium.py
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class SeleniumTest:
    def __init__(self):
        # Lazy init: só cria o driver quando instanciar a classe (não no import)
        chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/chromium")
        chromedriver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

        opts = Options()
        # Headless novo
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-software-rasterizer")
        opts.add_argument("--window-size=1920,1080")
        # Garante caminho do binário quando for Chromium
        opts.binary_location = chrome_bin

        service = Service(executable_path=chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=opts)

    def get(self, url: str):
        self.driver.get(url)
        return self.driver.title

    def quit(self):
        try:
            self.driver.quit()
        except Exception:
            pass
