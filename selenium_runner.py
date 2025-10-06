# selenium_runner.py
import os, time, threading, platform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Lock para serializar no free tier e evitar 2 Chromes ao mesmo tempo
_driver_lock = threading.Lock()

def _is_container() -> bool:
    """Heurística simples para detectar container."""
    return os.path.exists("/.dockerenv") or os.path.exists("/usr/bin/chromium") or os.getenv("CONTAINER") == "1"

def _build_options(container: bool) -> Options:
    opts = Options()
    # Headless em ambos para consistência
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1200,900")

    if container:
        # Ambiente Linux do container (Koyeb/Docker)
        opts.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")
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
        # Reduz consumo (imagens off + eager)
        opts.add_argument("--blink-settings=imagesEnabled=false")
        opts.page_load_strategy = "eager"
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        }
        opts.add_experimental_option("prefs", prefs)
    else:
        # Local (Windows/macOS/Linux fora do container)
        # Não fixar binary_location à toa: deixe o Chrome padrão do SO
        # Se quiser forçar um Chrome portátil, use CHROME_BIN apontando para .exe
        chrome_bin = os.getenv("CHROME_BIN")
        if chrome_bin and os.path.exists(chrome_bin):
            opts.binary_location = chrome_bin
        # Mantemos leve:
        opts.add_argument("--disable-extensions")
        opts.page_load_strategy = "eager"

    return opts

def _new_driver():
    container = _is_container()
    options = _build_options(container)

    if container:
        # Caminho do chromedriver no container (instalado via apt no Dockerfile)
        driver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
        if not os.path.exists(options.binary_location):
            raise RuntimeError(f"Chromium não encontrado em: {options.binary_location}")
        if not os.path.exists(driver_path):
            raise RuntimeError(f"Chromedriver não encontrado em: {driver_path}")
        service = Service(executable_path=driver_path)
        return webdriver.Chrome(service=service, options=options)
    else:
        # Fora do container: usar Selenium Manager (não precisa do driver_path)
        # Requer Google Chrome instalado no sistema.
        return webdriver.Chrome(options=options)

def quick_visit(url: str = "https://example.com") -> dict:
    with _driver_lock:  # serializa chamadas
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
                time.sleep(1.5)
            finally:
                try:
                    if d: d.quit()
                except Exception:
                    pass
