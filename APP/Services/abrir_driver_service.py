from time import sleep
from APP.Config.ihs_config import _ensure_driver
import pyautogui

def abrir_driver_main():
    driver, wdw, PASTA_DOWNLOAD = _ensure_driver()

    driver.execute_script("document.body.style.zoom='75%'")
    
    pyautogui.PAUSE = 3
    
    # driver.execute_script("document.body.style.zoom='75%'")

    pyautogui.click(1520, 364)  # Clicar em adicionar a extensão ao Chrome
    # pyautogui.click(1167, 256)  # Clicar em adicionar a extensão ao Chrome

    pyautogui.click(1002, 300)  # Clica para configurar a extensão

    sleep(6)
    pyautogui.click(1777, 78)  # Clica para configurar a extensão
    pyautogui.click(1534, 275)
    pyautogui.click(1679, 223)
    pyautogui.click(1683, 335)
    pyautogui.click(1674, 513, clicks=2, duration=1)
    pyautogui.write('2000')
    pyautogui.click(1071, 517)
    # pyautogui.click(1596, 61)  # Clica para configurar a extensão
    # pyautogui.click(1596, 61)  # Clica para configurar a extensão
    # pyautogui.click(1408, 219)
    # pyautogui.click(1513, 180)
    # pyautogui.click(1514, 268)
    # pyautogui.click(1510, 411, clicks=2, duration=1)
    # pyautogui.write('2000')
    # pyautogui.click(1073, 385)


