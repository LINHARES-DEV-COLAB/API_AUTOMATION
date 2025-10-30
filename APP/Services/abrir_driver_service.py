from time import sleep
from APP.Config.ihs_config import _ensure_driver
import pyautogui

def abrir_driver_main():
    driver, wdw, PASTA_DOWNLOAD = _ensure_driver()
    
    pyautogui.PAUSE = 3

    sleep(3)
    pyautogui.click(1211, 294, duration=1)  # Clicar em adicionar a extensão ao Chrome

    sleep(3)
    pyautogui.click(829, 245, duration=1)

    sleep(6)
    pyautogui.click(1422, 61, duration=1)  # Clica para configurar a extensão
    pyautogui.click(1221, 216, duration=1)
    pyautogui.click(1348, 179, duration=1)
    pyautogui.click(1344, 272, duration=1)
    pyautogui.click(1342, 410, clicks=2, duration=1)
    pyautogui.write('2000')
    pyautogui.click(865, 390, duration=1)


