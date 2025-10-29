from time import sleep
from APP.Config.ihs_config import _ensure_driver
import pyautogui

def abrir_driver_main():
    driver, wdw, PASTA_DOWNLOAD = _ensure_driver()

    driver.execute_script("document.body.style.zoom='75%'")
    
    sleep(3)
    pyautogui.click(1167, 256)  # Clicar em adicionar a extensão ao Chrome

    sleep(3)
    centro_add = pyautogui.locateCenterOnScreen(image='APP/static/img/btn_add_extension.PNG')
    pyautogui.click(*centro_add)

    sleep(6)

    pyautogui.click(1596, 61)  # Clica para configurar a extensão
    pyautogui.click(1408, 219)
    pyautogui.click(1513, 180)
    pyautogui.click(1514, 268)
    pyautogui.click(1510, 411, clicks=2, duration=1)
    pyautogui.write('2000')
    pyautogui.click(1073, 385)


