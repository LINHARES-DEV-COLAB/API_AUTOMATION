# selenium_runner.py
import os, time, threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service  # << IMPORTANTE

# lock p/ serializar chamadas (evita 2 Chromes simultâneos no free)
_driver_lock = threading.Lock()

def _build_options() -> Options:
    opts = Options()
    opts.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    # Headless e flags leves p/ container
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
    # desliga imagens: reduz memória
    opts.add_argument("--blink-settings=imagesEnabled=false")
    opts.page_load_strategy = "eager"

    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    }
    opts.add_experimental_option("prefs", prefs)
    return opts

def _new_driver():
    driver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    service = Service(executable_path=driver_path)   # << AQUI
    options = _build_options()
    return webdriver.Chrome(service=service, options=options)  # << AQUI

def quick_visit(url: str = "https://example.com") -> dict:
    with _driver_lock:
        for attempt in (1, 2):
            d = None
            try:
                d = _new_driver()
                d.set_page_load_timeout(60)
                d.get(url)
                return {"ok": True, "title": d.title, "url": d.current_url}
            except Exception as e:
                if attempt == 2:
                    return {"ok": False, "error": f"{e}"}
                time.sleep(1.5)  # pequeno backoff
            finally:
                try:
                    if d:
                        d.quit()
                except Exception:
                    pass
