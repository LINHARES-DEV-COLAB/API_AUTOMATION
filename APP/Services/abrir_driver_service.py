from APP.Config.ihs_config import _ensure_driver
from tkinter import messagebox

def abrir_driver_main():
    driver, wdw, PASTA_DOWNLOAD = _ensure_driver()
    
    resposta = True
    while resposta:
        resposta = messagebox.askyesno(title='Extensão', message='Você já adicionou a extensão?')
        if resposta: break
        continue


