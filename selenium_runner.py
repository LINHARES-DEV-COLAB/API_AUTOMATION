import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def build_chrome():
    chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    driver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

    if not os.path.exists(chrome_bin):
        raise RuntimeError(f"Chrome não encontrado em: {chrome_bin}")
    if not os.path.exists(driver_path):
        raise RuntimeError(f"Chromedriver não encontrado em: {driver_path}")

    opts = Options()
    # Flags cruciais em container (Render)
    opts.binary_location = chrome_bin
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-software-rasterizer")
    opts.add_argument("--window-size=1920,1080")

    # Se quiser desabilitar imagens para acelerar:
    # prefs = {"profile.managed_default_content_settings.images": 2}
    # opts.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(driver_path, options=opts)
    return driver

def quick_visit(url: str = "https://www.google.com") -> dict:
    """Abre, visita, retorna título e fecha."""
    driver = build_chrome()
    try:
        driver.get(url)
        return {"ok": True, "title": driver.title, "url": driver.current_url}
    finally:
        # SEMPRE fechar para não vazar processos
        driver.quit()
