from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os, time, threading

def build_chrome():
    opts = Options()
    opts.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")
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
    opts.add_argument("--blink-settings=imagesEnabled=false")
    opts.page_load_strategy = "eager"

    driver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

    # ✅ Selenium 4: passe o driver via Service (ou deixe sem para Selenium Manager)
    if driver_path and os.path.exists(driver_path):
        service = Service(executable_path=driver_path)
        return webdriver.Chrome(service=service, options=opts)
    else:
        # fallback (local com Chrome instalado): Selenium Manager escolhe o driver
        return webdriver.Chrome(options=opts)

# Serializa chamadas para não abrir 2 Chromes em free tier
_driver_lock = threading.Lock()

def quick_visit(url: str = "https://example.com") -> dict:
    with _driver_lock:
        for attempt in (1, 2):
            d = None
            try:
                d = build_chrome()
                d.set_page_load_timeout(60)
                d.get(url)
                return {"ok": True, "title": d.title, "url": d.current_url}
            except Exception as e:
                if attempt == 2:
                    return {"ok": False, "error": f"{e}"}
                time.sleep(1.5)
            finally:
                try:
                    if d: d.quit()
                except Exception:
                    pass
