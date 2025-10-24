from __future__ import annotations
from typing import Iterable, Tuple, Union, Optional, Dict, List, Set
import logging
import psutil
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException, NoSuchElementException
)
from selenium.webdriver import ActionChains
from time import sleep
# Configure logging
LOGGER = logging.getLogger('selenium.webdriver.remote.remote_connection')
LOGGER.setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Opcional: se Paths/LoginDTO existirem no projeto, manter compatibilidade
try:
    from core.config import Paths  # type: ignore
except Exception:  # pragma: no cover - ambiente de teste sem Paths
    class _Dummy: pass
    Paths = _Dummy()  # fallback para não quebrar import
try:
    from DTO.user_dto import LoginDTO  # type: ignore
except Exception:  # pragma: no cover
    class LoginDTO:  # fallback mínimo p/ testes
        def __init__(self, usuario: str = "", senha: str = "", url: Optional[str] = None, site_url: Optional[str] = None):
            self.usuario = usuario
            self.senha = senha
            self.url = url
            self.site_url = site_url


# ------------------------------------------
# Utils fora da classe
# ------------------------------------------

def _wait_overlay_gone(driver: webdriver.Chrome, timeout: int = 15) -> None:
    """Espera sumir overlay comum (gx-mask / Angular CDK). Melhor esforço."""
    sel = "div#MASK.gx-mask, .gx-mask, .cdk-overlay-backdrop.cdk-overlay-backdrop-showing"
    try:
        WebDriverWait(driver, 0.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
        WebDriverWait(driver, timeout).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, sel)))
    except TimeoutException:
        pass

def _find_in_frames(driver: webdriver.Chrome, locator: Tuple[str, str], timeout: int = 8) -> tuple[WebElement, Optional[int]]:
    """Procura no root e, se não achar, tenta iframes. Retorna (el, idx_iframe|None)."""
    driver.switch_to.default_content()
    try:
        el = WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
        return el, None
    except TimeoutException:
        pass

    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for idx, frm in enumerate(iframes):
        driver.switch_to.default_content()
        WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it(frm))
        try:
            el = WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))
            return el, idx
        except TimeoutException:
            continue

    driver.switch_to.default_content()
    raise NoSuchElementException("Elemento não encontrado nem no root nem em iframes.")

def click_next_paginator(driver: webdriver.Chrome, timeout: int = 15) -> None:
    """
    Clique resiliente no botão 'Próximo' do MatPaginator (fora da classe para uso avulso).
    - Overlay-aware, iFrame-aware, scroll + Actions + JS + dispatchEvent
    - Checa disabled/aria-disabled; espera staleness de uma linha da tabela
    """
    _wait_overlay_gone(driver, timeout=timeout)

    locator = (By.CSS_SELECTOR, 'button.mat-paginator-navigation-next[aria-label="Próximo"]')
    el, _ = _find_in_frames(driver, locator, timeout=8)

    # aguarda ficar clicável (se falhar, seguimos com fallback manual)
    try:
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
    except TimeoutException:
        pass

    # estado disabled?
    aria_disabled = (el.get_attribute("aria-disabled") or "").strip().lower()
    has_disabled = el.get_attribute("disabled") is not None
    if aria_disabled == "true" or has_disabled:
        raise RuntimeError("O botão 'Próximo' está desabilitado (provável última página).")

    # elemento de referência para detectar mudança
    try:
        first_row = driver.find_element(By.CSS_SELECTOR, "table tbody tr")
    except Exception:
        first_row = None

    # clique resiliente
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", el)
    except Exception:
        pass

    try:
        _wait_overlay_gone(driver, timeout=timeout)
        el.click()
    except (ElementClickInterceptedException, StaleElementReferenceException, TimeoutException):
        try:
            _wait_overlay_gone(driver, timeout=timeout)
            ActionChains(driver).move_to_element(el).pause(0.05).click().perform()
        except Exception:
            try:
                _wait_overlay_gone(driver, timeout=timeout)
                driver.execute_script("arguments[0].click();", el)
            except Exception:
                driver.execute_script("""
                    const e = arguments[0];
                    const ev = new MouseEvent('click', {bubbles:true, cancelable:true, view:window});
                    e.dispatchEvent(ev);
                """, el)

    # espera re-render
    wait = WebDriverWait(driver, timeout)
    try:
        if first_row is not None:
            wait.until(EC.staleness_of(first_row))
        else:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
    except TimeoutException:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody")))


# ------------------------------------------
# Tipos
# ------------------------------------------

Locator = Union[str, Tuple[str, str], Iterable[Tuple[str, str]]]


# ------------------------------------------
# Classe principal
# ------------------------------------------

class SeleniumIntegration:
    def __init__(self, timeout: int = 20):
        self.driver: Optional[webdriver.Chrome] = None
        self.timeout = timeout
        # ⭐ NOVO: Timeouts específicos para operações críticas
        self.page_load_timeout = 30
        self.script_timeout = 20

    # ---------- Infra ----------
    def start(self) -> None:
        if self.driver is not None:
            return
    
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
    
    # ⭐ CONFIGURAÇÕES OTIMIZADAS PARA CARREGAMENTOS LENTOS
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--memory-pressure-off")
        options.add_argument("--max_old_space_size=4096")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-logging")
        options.add_argument("--start-maximized")
        
        # ⭐ NOVAS CONFIGURAÇÕES PARA TIMEOUT
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Capture performance logs
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
        try:
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # ⭐ AUMENTAR TIMEOUTS PARA CARREGAMENTOS LENTOS
            self.driver.set_page_load_timeout(60)  # Aumentado para 60 segundos
            self.driver.set_script_timeout(30)
            
            logging.info("Driver Chrome iniciado com sucesso")
        except Exception as e:
            logging.error(f"Erro crítico ao iniciar driver: {e}")
            raise

    def close(self) -> None:
        if self.driver:
            self.driver.quit()
            self.driver = None
            logging.info("Driver Chrome fechado")

    def _check_driver_alive(self) -> bool:
        """Verifica se o driver ainda está responsivo"""
        if self.driver is None:
            return False
        
        try:
            # Testa se o driver responde
            self.driver.current_url
            return True
        except Exception:
            logging.warning("Driver não está mais responsivo")
            return False

    def _safe_operation(self, operation_func, *args, **kwargs):
        """Executa operação com verificação de driver ativo"""
        if not self._check_driver_alive():
            raise RuntimeError("Driver não está mais disponível")
        
        return operation_func(*args, **kwargs)

    def _check_memory_usage(self):
        """Monitora uso de memória"""
        try:
            process = psutil.Process(os.getpid())
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            if memory_usage > 500:  # ⚠️ Alerta se usar mais de 500MB
                logging.warning(f"Alto uso de memória: {memory_usage:.2f}MB")
        except Exception:
            pass  # Ignora erros de monitoramento

    def _wait_dom_ready(self, timeout: Optional[int] = None) -> None:
        d = self.driver
        assert d is not None, "Driver não inicializado"
        to = timeout or self.timeout
        WebDriverWait(d, to).until(lambda drv: drv.execute_script("return document.readyState") == "complete")

    def _to_locator_list(self, locs: Locator) -> List[Tuple[str, str]]:
        if isinstance(locs, str):
            return [(By.XPATH, locs)]
        if isinstance(locs, tuple):
            return [locs]
        return list(locs)

    def _find_with_fallbacks(self, locs: Locator, timeout: Optional[int] = None, need_clickable: bool = False) -> WebElement:
        return self._safe_operation(self._find_with_fallbacks_impl, locs, timeout, need_clickable)
    
    def _find_with_fallbacks_impl(self, locs: Locator, timeout: Optional[int] = None, need_clickable: bool = False) -> WebElement:
        d = self.driver
        assert d is not None, "Driver não inicializado"
        to = timeout or self.timeout
        loc_list = self._to_locator_list(locs)
        last_err: Optional[Exception] = None
        for by, sel in loc_list:
            try:
                cond = EC.element_to_be_clickable if need_clickable else EC.visibility_of_element_located
                return WebDriverWait(d, to).until(cond((by, sel)))
            except Exception as e:
                last_err = e
        assert last_err is not None
        raise last_err

    def _try_in_iframes(self, locs: Locator, timeout: Optional[int] = None, need_clickable: bool = False) -> WebElement:
        return self._safe_operation(self._try_in_iframes_impl, locs, timeout, need_clickable)
    
    def _try_in_iframes_impl(self, locs: Locator, timeout: Optional[int] = None, need_clickable: bool = False) -> WebElement:
        d = self.driver
        assert d is not None, "Driver não inicializado"
        d.switch_to.default_content()

        # tenta no documento raiz
        try:
            return self._find_with_fallbacks(locs, timeout=timeout, need_clickable=need_clickable)
        except Exception:
            pass

        # percorre iframes
        frames = d.find_elements(By.TAG_NAME, "iframe")
        for fr in frames:
            d.switch_to.default_content()
            d.switch_to.frame(fr)
            try:
                return self._find_with_fallbacks(locs, timeout=max(3, (timeout or self.timeout)//2), need_clickable=need_clickable)
            except Exception:
                continue

        d.switch_to.default_content()
        # última tentativa: raiz com presence
        return self._find_with_fallbacks(locs, timeout=timeout, need_clickable=False)

    def _safe_click(self, locs: Locator, timeout: Optional[int] = None) -> None:
        return self._safe_operation(self._safe_click_impl, locs, timeout)
    
    def _safe_click_impl(self, locs: Locator, timeout: Optional[int] = None) -> None:
        d = self.driver
        assert d is not None, "Driver não inicializado"
        try:
            el = self._try_in_iframes(locs, timeout=timeout, need_clickable=True)
        except Exception:
            el = self._try_in_iframes(locs, timeout=timeout, need_clickable=False)

        try:
            d.execute_script("arguments[0].scrollIntoView({block:'center',inline:'nearest'});", el)
        except Exception:
            pass

        try:
            el.click()
            return
        except Exception:
            pass

        try:
            d.execute_script("arguments[0].click();", el)
            return
        except Exception:
            pass

        try:
            el.send_keys(Keys.ENTER)
        except Exception as e:
            raise e

    # ---------- Fluxos ----------
    def login(self, dto: LoginDTO, url: Optional[str] = None, timeout: Optional[int] = None) -> None:
        """Login resiliente com suporte a URL (parâmetro > dto.url > dto.site_url > Paths.Url.url)."""
        if self.driver is None:
            self.start()
        d = self.driver
        assert d is not None, "Driver não inicializado"
        to = timeout or self.timeout

        # 1) Resolve URL
        target_url = (url or getattr(dto, "url", None) or getattr(dto, "site_url", None))
        try:
            if not target_url and hasattr(Paths, "Url") and hasattr(Paths.Url, "url"):
                target_url = Paths.Url.url  # type: ignore
        except Exception:
            pass

        if target_url:
            try:
                print(f"🌐 Acessando: {target_url}")
                d.get(str(target_url))
                # Aguarda um pouco mais para carregamento completo
                WebDriverWait(d, 60).until(lambda drv: drv.execute_script("return document.readyState") == "complete")
                print("✅ Página carregada com sucesso")
            except TimeoutException:
                print("⚠️  Página demorou para carregar, mas continuando...")
            except Exception as e:
                print(f"⚠️  Erro ao carregar página: {e}, continuando...")

    # ... resto do código do login permanece igual ...

        # 2) Candidatos (Paths se existir + fallbacks comuns)
        user_sel: List[Tuple[str, str]] = []
        pass_sel: List[Tuple[str, str]] = []
        submit_sel: List[Tuple[str, str]] = []
        try:
            if hasattr(Paths, "Login") and hasattr(Paths.Login, "username"):
                user_sel.append((By.XPATH, Paths.Login.username))  # type: ignore
            if hasattr(Paths, "Login") and hasattr(Paths.Login, "password"):
                pass_sel.append((By.XPATH, Paths.Login.password))  # type: ignore
            if hasattr(Paths, "Login") and hasattr(Paths.Login, "submit"):
                submit_sel.append((By.XPATH, Paths.Login.submit))  # type: ignore
        except Exception:
            pass

        user_sel += [
            (By.CSS_SELECTOR, "input[formcontrolname='username']"),
            (By.CSS_SELECTOR, "input[name='username']"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.XPATH, "//input[contains(@id,'mat-input') and not(@type='password')]"),
        ]
        pass_sel += [
            (By.CSS_SELECTOR, "input[formcontrolname='password']"),
            (By.CSS_SELECTOR, "input[name='password']"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.XPATH, "//input[contains(@id,'mat-input') and @type='password']"),
        ]
        submit_sel += [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[.//span[contains(translate(.,'ENTRARLOGIN','entrarlogin'),'entrar')] or contains(., 'Login')]"),
            (By.XPATH, "//button[contains(., 'Entrar') or contains(., 'Acessar') or contains(., 'Login')]"),
        ]

        def _first_present(locs: List[Tuple[str, str]]) -> Optional[WebElement]:
            for by, sel in locs:
                try:
                    return WebDriverWait(d, max(4, to//3)).until(EC.presence_of_element_located((by, sel)))
                except Exception:
                    continue
            return None

        user_el = _first_present(user_sel)
        pass_el = _first_present(pass_sel)

        if user_el:
            try: user_el.clear()
            except Exception: pass
            user_el.send_keys(getattr(dto, "usuario", None) or getattr(dto, "email", None) or "")

        if pass_el:
            try: pass_el.clear()
            except Exception: pass
            pass_el.send_keys(getattr(dto, "senha", None) or getattr(dto, "password", None) or "")

        btn = _first_present(submit_sel)
        if btn:
            try:
                # usa o clique seguro via locator calculado (para manter iFrame aware)
                self._safe_click([(By.XPATH, ".//self::button")], timeout=max(8, to//2))  # best effort
            except Exception:
                try: btn.submit()
                except Exception: pass
        elif pass_el:
            try: pass_el.send_keys(Keys.ENTER)
            except Exception: pass

        # Espera pós-login (melhor esforço)
        try:
            WebDriverWait(d, max(6, to)).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
        except Exception:
            pass

    ##################################################################################################################    

    def clica_no_modulo_fidc(self, locators: Optional[Locator] = None, text_hint: Optional[str] = "FloorPlan") -> None:
        d = self.driver
        assert d is not None, "Driver não inicializado"
        
        sleep(2)
        
        print("🔍 Procurando elemento FloorPlan específico...")
        
        # Seletores específicos baseados no debug
        cand = [
            # Elemento específico do dropdown do FloorPlan
            (By.XPATH, "//a[@class='nav-link nav-dropdown-toggle' and contains(., 'FloorPlan')]"),
            (By.XPATH, "//app-sidebar-nav-dropdown[contains(., 'FloorPlan')]//a"),
            (By.CSS_SELECTOR, "a.nav-link.nav-dropdown-toggle"),
        ]

        elemento_encontrado = None
        for by, selector in cand:
            try:
                elements = WebDriverWait(d, 10).until(
                    EC.presence_of_all_elements_located((by, selector))
                )
                for el in elements:
                    if "FloorPlan" in el.text and el.is_displayed() and el.is_enabled():
                        elemento_encontrado = el
                        print(f"✅ Elemento específico encontrado: {el.text}")
                        print(f"   Classe: {el.get_attribute('class')}")
                        break
                if elemento_encontrado:
                    break
            except Exception as e:
                continue

        if not elemento_encontrado:
            raise TimeoutException("Não consegui encontrar o módulo FloorPlan específico")

        # Tenta abrir o dropdown
        try:
            print("🔄 Abrindo dropdown do FloorPlan...")
            d.execute_script("arguments[0].click();", elemento_encontrado)
            sleep(2)  # Aguarda o dropdown abrir
            
            # Verifica se o dropdown abriu (muda o estado)
            aria_expanded = elemento_encontrado.get_attribute('aria-expanded')
            print(f"   Estado do dropdown: aria-expanded='{aria_expanded}'")
            
        except Exception as e:
            print(f"⚠️  Erro ao abrir dropdown: {e}")
            raise



    def clica_em_aberto(self) -> None:
        """Entra na tela 'Em Aberto' - versão corrigida"""
        d = self.driver
        assert d is not None, "Driver não inicializado"
        
        print("🔍 Procurando 'Em Aberto' no dropdown aberto...")
        
        # Agora sabemos exatamente onde está: dentro do dropdown do FloorPlan
        selectors = [
            # Seletor específico baseado no debug
            "//app-sidebar-nav-dropdown[contains(., 'FloorPlan')]//a[contains(., 'Em Aberto')]",
            "//app-sidebar-nav-items//a[contains(., 'Em Aberto')]",
            "//a[contains(., 'Em Aberto') and contains(@class, 'nav-link')]",
        ]
        
        for selector in selectors:
            try:
                elemento = WebDriverWait(d, 10).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                print(f"✅ 'Em Aberto' encontrado: {elemento.text}")
                print(f"   Classe: {elemento.get_attribute('class')}")
                
                # Clica
                d.execute_script("arguments[0].click();", elemento)
                sleep(3)
                
                # Verifica se navegou
                current_url = d.current_url
                print(f"🔗 Navegado para: {current_url}")
                
                if "aberto" in current_url.lower():
                    print("✅ Navegação para 'Em Aberto' confirmada!")
                else:
                    print("ℹ️  Navegou para outra página")
                    
                return
            except Exception as e:
                print(f"❌ Não encontrado com: {selector} - {e}")
        
        print("❌ Não foi possível encontrar 'Em Aberto'")
        raise TimeoutException("'Em Aberto' não encontrado após abrir dropdown")
    # ---------- Autocomplete Angular Material ----------
    def insere_revenda(self, termo: str, texto_completo: Optional[str] = None, prefix_len: int = 6) -> None:
        """Interage com mat-autocomplete 'Revenda' se Paths existir; senão é no-op amigável."""
        d = self.driver
        assert d is not None, "Driver não inicializado"
        to = self.timeout
        try:
            campo = self._find_with_fallbacks(Paths.Inputs.input_revenda, timeout=max(8, to//2), need_clickable=False)  # type: ignore
        except Exception:
            return  # sem Paths, não tenta adivinhar

        base = (texto_completo or termo).strip()
        prefixo = base[:max(1, prefix_len)]
        if prefixo:
            campo.send_keys(prefixo)

        panel_id = campo.get_attribute("aria-controls")
        if panel_id:
            panel = WebDriverWait(d, to).until(EC.visibility_of_element_located((By.ID, panel_id)))
        else:
            WebDriverWait(d, to).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".mat-autocomplete-panel.mat-autocomplete-visible")))
            panels = d.find_elements(By.CSS_SELECTOR, ".mat-autocomplete-panel.mat-autocomplete-visible")
            if not panels:
                raise TimeoutError("Autocomplete não abriu.")
            panel = panels[-1]

        options = panel.find_elements(By.CSS_SELECTOR, "mat-option")
        candidatos: List[tuple[str, WebElement]] = []
        for opt in options:
            txt = (opt.text or "").strip()
            if not txt or txt.lower() == "revenda":
                continue
            candidatos.append((txt, opt))
        if not candidatos:
            raise TimeoutError("Nenhuma opção de revenda encontrada.")

        alvo_txt, alvo_el = None, None
        if texto_completo:
            for txt, el in candidatos:
                if txt.strip() == texto_completo.strip():
                    alvo_txt, alvo_el = txt, el
                    break
        if alvo_el is None:
            term = termo.strip().lower()
            for txt, el in candidatos:
                if term and term in txt.lower():
                    alvo_txt, alvo_el = txt, el
                    break
        if alvo_el is None:
            alvo_txt, alvo_el = candidatos[0]

        try:
            d.execute_script("arguments[0].scrollIntoView({block:'center',inline:'nearest'});", alvo_el)
        except Exception:
            pass
        try:
            alvo_el.click()
        except Exception:
            d.execute_script("arguments[0].click();", alvo_el)

        WebDriverWait(d, to).until(
            lambda _:
                (campo.get_attribute("value") and termo[:3].lower() in (campo.get_attribute("value") or "").lower())
                or (texto_completo and (campo.get_attribute("value") == texto_completo))
        )

    def clica_em_pesquisa(self) -> None:
        """Clica no botão Pesquisar (se Paths existir), com fallback brando."""
        try:
            self._safe_click(Paths.Inputs.btn_pesquisar, timeout=max(8, self.timeout//2))  # type: ignore
        except Exception:
            # fallback por texto
            try:
                self._safe_click([(By.XPATH, "//button[contains(., 'Pesquisar')]"),
                                  (By.XPATH, "//button[.//span[contains(., 'Pesquisar')]]")],
                                 timeout=max(8, self.timeout//2))
            except Exception:
                pass

    # ---------- Paginator helpers ----------
    def _goto_first_page(self) -> None:
        d = self.driver
        assert d is not None, "Driver não inicializado"
        btn_first = d.find_elements(By.CSS_SELECTOR, ".mat-paginator .mat-paginator-navigation-first")
        if btn_first:
            try:
                btn_first[0].click()
            except Exception:
                d.execute_script("arguments[0].click();", btn_first[0])
            WebDriverWait(d, max(5, self.timeout//2)).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody"))
            )

    def _paginator_next_enabled(self) -> bool:
        d = self.driver
        assert d is not None, "Driver não inicializado"
        try:
            btn_next = d.find_element(By.CSS_SELECTOR, ".mat-paginator .mat-paginator-navigation-next")
        except Exception:
            return False
        return (btn_next.get_attribute("disabled") is None) and ((btn_next.get_attribute("aria-disabled") or "").lower() != "true")

    def _paginator_next_js(self) -> bool:
        """Alternativa JS para avançar página"""
        script = """
        const nextButtons = document.querySelectorAll('button.mat-paginator-navigation-next');
        for (let btn of nextButtons) {
            if (!btn.disabled && btn.getAttribute('aria-disabled') !== 'true') {
                btn.click();
                return true;
            }
        }
        return false;
        """
        try:
            result = self.driver.execute_script(script)
            return bool(result)
        except Exception as e:
            logging.warning(f"Erro no _paginator_next_js: {e}")
            return False

    def _paginator_next_action_chains(self) -> bool:
        """Usa ActionChains para clique no paginador"""
        try:
            btn_next = self.driver.find_element(By.CSS_SELECTOR, ".mat-paginator .mat-paginator-navigation-next")
            if btn_next.get_attribute("disabled") is None:
                ActionChains(self.driver).move_to_element(btn_next).click().perform()
                return True
        except Exception as e:
            logging.warning(f"Erro no _paginator_next_action_chains: {e}")
        return False

    def _paginator_next_click(self) -> bool:
        script = """
        const buttons = document.querySelectorAll('button');
        for (let btn of buttons) {
            const label = btn.getAttribute('aria-label') || btn.textContent || '';
            if ((label.includes('Próximo') || label.includes('Next')) && !btn.disabled) {
                btn.click();
                return true;
            }
        }
        return false;
        """
        
        try:
            result = self.driver.execute_script(script)
            return bool(result)
        except Exception as e:
            logging.warning(f"Erro ao executar script: {e}")
            return False

    def _safe_paginator_next(self) -> bool:
        """Tenta avançar página com múltiplas estratégias"""
        strategies = [
            self._paginator_next_click,
            self._paginator_next_js,
            self._paginator_next_action_chains
        ]
        
        for strategy in strategies:
            try:
                if strategy():
                    # Aguarda carregamento da nova página
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
                    )
                    return True
            except Exception as e:
                logging.warning(f"Estratégia {strategy.__name__} falhou: {e}")
                continue
        
        return False

    # ---------- Busca/Marca NF ----------
    def _buscar_nota_na_pagina(self, nf: str) -> Optional[WebElement]:
        d = self.driver
        assert d is not None, "Driver não inicializado"
        xpath_row = f"//table//tbody//tr[.//td[normalize-space(.)='{nf}']]"
        try:
            return WebDriverWait(d, max(4, self.timeout//3)).until(
                EC.presence_of_element_located((By.XPATH, xpath_row))
            )
        except Exception:
            return None

    def _marcar_checkbox_da_linha(self, row_el: WebElement) -> bool:
        d = self.driver
        assert d is not None, "Driver não inicializado"
        # 1) botão padrão usado no seu DOM
        try:
            cb = row_el.find_element(By.CSS_SELECTOR, "button[name^='idNotaFiscal_']")
            if cb.get_attribute("disabled") is None:
                try:
                    cb.click()
                except Exception:
                    d.execute_script("arguments[0].click();", cb)
                return True
        except Exception:
            pass
        # 2) fallback: checkbox material/input
        for sel in ("mat-checkbox input[type='checkbox']", "input[type='checkbox']"):
            try:
                cb2 = row_el.find_element(By.CSS_SELECTOR, sel)
                if cb2.is_enabled() and not cb2.is_selected():
                    try:
                        cb2.click()
                    except Exception:
                        d.execute_script("arguments[0].click();", cb2)
                return True
            except Exception:
                continue
        # 3) botão genérico
        try:
            btn_any = row_el.find_elements(By.CSS_SELECTOR, "button")
            if btn_any:
                b0 = btn_any[0]
                if b0.get_attribute("disabled") is None:
                    try:
                        b0.click()
                    except Exception:
                        d.execute_script("arguments[0].click();", b0)
                    return True
        except Exception:
            pass
        return False

    def _marcar_nf_paginada(self, nf: str) -> bool:
        """Procura a NF em todas as páginas até encontrar ou até a última página"""
        pagina_atual = 1
        max_paginas = 50  # ⭐ Safe guard contra loop infinito
        
        while pagina_atual <= max_paginas:
            try:
                self._check_memory_usage()  # ⭐ Monitora memória
                
                self._wait_dom_ready(timeout=10)
                
                # Procura a NF na página atual
                row = self._buscar_nota_na_pagina(nf)
                if row is not None:
                    if self._marcar_checkbox_da_linha(row):
                        logging.info(f"✅ NF {nf} encontrada e marcada na página {pagina_atual}")
                        return True
                
                # Verifica se pode avançar
                if not self._paginator_next_enabled():
                    logging.info(f"❌ NF {nf} não encontrada nas {pagina_atual} páginas disponíveis")
                    return False
                
                # Tenta avançar com tratamento robusto
                if not self._safe_paginator_next():
                    logging.warning(f"⚠️ Não foi possível avançar para próxima página")
                    return False
                    
                pagina_atual += 1
                logging.info(f"🔍 Indo para página {pagina_atual}...")
                
            except Exception as e:
                logging.error(f"❌ Erro na página {pagina_atual}: {e}")
                return False
        
        logging.warning(f"⚠️ Limite de {max_paginas} páginas atingido")
        return False

    # Público: marca diversas NFs (mantém página de forma eficiente)
    def marcar_nfs_do_emp(self, nfs: List[str]) -> Dict[str, bool]:
        """Para cada NF, procura e marca (se possível). Retorna dict {NF: True/False}. Começa da primeira página."""
        self._goto_first_page()
        resultados: Dict[str, bool] = {}
        
        for nf in nfs:
            if not self._check_driver_alive():
                raise RuntimeError("Driver crashou durante a execução")
            resultados[nf] = self._marcar_nf_paginada(nf)
        
        return resultados

    # ---------- Alertas/Popups ----------
    def confere_alerta_boleto_aberto(self, timeout: Optional[int] = None) -> bool:
        d = self.driver
        assert d is not None, "Driver não inicializado"
        to = timeout or self.timeout
        try:
            WebDriverWait(d, to).until(
                EC.visibility_of_element_located((By.XPATH, Paths.OutstandingTitles.div_alerta_boleto_aberto))  # type: ignore
            )
            return True
        except Exception:
            return False

    def fecha_popup(self, timeout: Optional[int] = None) -> bool:
        """Fecha popup com múltiplas estratégias de fallback"""
        d = self.driver
        assert d is not None, "Driver não inicializado"
        to = timeout or self.timeout
        
        # Estratégias para fechar popup
        close_selectors = []
        
        # 1. Primeiro tenta pelo Paths se existir
        try:
            if hasattr(Paths, "Inputs") and hasattr(Paths.Inputs, "btn_fechar"):
                close_selectors.append((By.XPATH, Paths.Inputs.btn_fechar))  # type: ignore
        except Exception:
            pass
        
        # 2. Fallbacks comuns para botões de fechar
        close_selectors.extend([
            (By.CSS_SELECTOR, "button[aria-label*='fechar' i]"),
            (By.CSS_SELECTOR, "button[class*='close' i]"),
            (By.XPATH, "//button[contains(., 'Fechar') or contains(., 'Close')]"),
            (By.CSS_SELECTOR, ".mat-dialog-actions button:first-child"),
            (By.CSS_SELECTOR, "button.mat-button, button.mat-raised-button"),
        ])
        
        # Tenta cada seletor
        for by, selector in close_selectors:
            try:
                close_buttons = d.find_elements(by, selector)
                for btn in close_buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        try:
                            self._safe_click([(by, selector)], timeout=5)
                            
                            # Verifica se o popup sumiu (melhor esforço)
                            try:
                                WebDriverWait(d, 3).until(
                                    EC.invisibility_of_element_located((by, selector))
                                )
                            except:
                                pass
                                
                            logging.info("Popup fechado com sucesso")
                            return True
                        except Exception:
                            continue
            except Exception:
                continue
        
        # 3. Fallback final: tecla ESC
        try:
            ActionChains(d).send_keys(Keys.ESCAPE).perform()
            logging.info("Tentativa de fechar popup com ESC")
            return True
        except Exception:
            pass
        
        logging.warning("Não foi possível fechar o popup")
        return False
    
# No arquivo selenium_integration.py, DENTRO da classe SeleniumIntegration, adicione:

    def abrir_menu_hamburguer(self) -> bool:
        """Abre o menu hamburguer se estiver fechado e visível"""
        d = self.driver
        assert d is not None, "Driver não inicializado"
        
        menu_selectors = [
            "button.navbar-toggler",
            ".navbar-toggler", 
            "button[class*='toggler']",
            "button[aria-label*='menu' i]",
            "button[aria-label*='abrir' i]",
            "button[type='button'][class*='navbar']"
        ]
        
        for selector in menu_selectors:
            try:
                elements = d.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        try:
                            print(f"🎯 Encontrado menu hamburguer: {selector}")
                            element.click()
                            sleep(1)  # Pequena pausa para menu abrir
                            return True
                        except Exception as e:
                            print(f"⚠️ Erro ao clicar no menu: {e}")
                            continue
            except Exception:
                continue
        
        print("ℹ️ Menu hamburguer não encontrado ou já está aberto")
        return False

    def debug_modulo_fidc(self):
        """Função de diagnóstico para o módulo FloorPlan (antigo FIDC)"""
        d = self.driver
        print("\n" + "="*50)
        print("🔍 DIAGNÓSTICO MÓDULO FLOORPLAN")
        print("="*50)
        
        # Verifica elementos com texto FloorPlan
        print("📋 Elementos com 'FloorPlan':")
        try:
            elementos = d.find_elements(By.XPATH, "//*[contains(text(), 'FloorPlan')]")
            for i, el in enumerate(elementos):
                try:
                    tag = el.tag_name
                    texto = el.text.strip() if el.text else "(vazio)"
                    print(f"  [{i}] <{tag}> '{texto}'")
                except:
                    print(f"  [{i}] Erro ao ler elemento")
        except Exception as e:
            print(f"  ERRO: {e}")
        
        # Verifica o elemento específico
        print("\n🎯 Elemento 'Módulo FloorPlan':")
        try:
            elemento = d.find_element(By.XPATH, "//a[contains(., 'Módulo FloorPlan')]")
            print(f"  ✅ ENCONTRADO: '{elemento.text}'")
            print(f"  Displayed: {elemento.is_displayed()}")
            print(f"  Enabled: {elemento.is_enabled()}")
            print(f"  Classes: {elemento.get_attribute('class')}")
        except Exception as e:
            print(f"  ❌ NÃO ENCONTRADO: {e}")
        
        print("="*50 + "\n")