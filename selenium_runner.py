from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os, time

def build_chrome():
    opts = Options()
    opts.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")

    # Headless em container "apertado"
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-software-rasterizer")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-background-networking")
    opts.add_argument("--disable-sync")
    opts.add_argument("--metrics-recording-only")
    opts.add_argument("--mute-audio")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--no-zygote")
    opts.add_argument("--renderer-process-limit=1")
    opts.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees,AutomationControlled,VizDisplayCompositor")
    opts.add_argument("--window-size=1200,900")
    # Desliga imagens para reduzir memória
    opts.add_argument("--blink-settings=imagesEnabled=false")
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    }
    opts.add_experimental_option("prefs", prefs)

    # Carregamento mais rápido/leve
    opts.page_load_strategy = "eager"  # tenta após DOMContentLoaded

    driver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    return webdriver.Chrome(driver_path, options=opts)

# Serialize as chamadas (evita 2 Chromes simultâneos)
import threading
_driver_lock = threading.Lock()

def quick_visit(url: str = "https://example.com") -> dict:
    attempts = 2
    with _driver_lock:
        for i in range(1, attempts + 1):
            d = None
            try:
                d = build_chrome()
                d.set_page_load_timeout(60)
                d.get(url)
                return {"ok": True, "title": d.title, "url": d.current_url}
            except Exception as e:
                if i == attempts:
                    return {"ok": False, "error": f"{e}"}
                time.sleep(1.5)  # backoff curto e tenta de novo
            finally:
                try:
                    if d: d.quit()
                except Exception:
                    pass
