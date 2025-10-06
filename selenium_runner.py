# selenium_runner.py
import os, time, threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

_driver_lock = threading.Lock()

def _build_options() -> Options:
    opts = Options()
    opts.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")

    # Headless e flags para container com pouca memória
    opts.add_argument("--headless")                 # (mais estável que --headless=new em alguns builds)
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
    opts.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees,AutomationControlled,VizDisplayCompositor,site-per-process,IsolateOrigins")
    opts.add_argument("--blink-settings=imagesEnabled=false")
    opts.add_argument("--proxy-server='direct://'")
    opts.add_argument("--proxy-bypass-list=*")
    opts.add_argument("--window-size=1200,900")

    # Não espere a página “completar” (economiza memória e tempo)
    opts.page_load_strategy = "none"
    return opts

def _new_driver():
    service = Service(executable_path=os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"))
    return webdriver.Chrome(service=service, options=_build_options())

def quick_visit(url: str = "https://example.com") -> dict:
    with _driver_lock:
        for attempt in (1, 2):
            d = None
            try:
                d = _new_driver()
                d.set_page_load_timeout(45)
                d.get(url)

                # pequena “folga” pro DOM subir o suficiente (sem esperar recursos pesados)
                time.sleep(0.6)

                # título via JS (não depende de load completo)
                title = d.execute_script("return document.title || ''") or ""
                cur = d.current_url
                return {"ok": True, "title": title, "url": cur}
            except Exception as e:
                if attempt == 2:
                    return {"ok": False, "error": f"{e}"}
                time.sleep(1.0)
            finally:
                try:
                    if d: d.quit()
                except Exception:
                    pass
