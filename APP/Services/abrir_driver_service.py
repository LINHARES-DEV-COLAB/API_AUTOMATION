from APP.Config.ihs_config import _ensure_driver
from tkinter import messagebox
from datetime import datetime

def abrir_driver_main():
    hoje = datetime.now().strftime('%d-%m-%Y')
    session_id = f'Abrindo o driver - {hoje}'
    driver, wdw, PASTA_DOWNLOAD = _ensure_driver(session_id)
    
    resposta = True
    while resposta:
        resposta = messagebox.askyesno(title='Extensão', message='Você já adicionou a extensão?')
        if resposta: break
        continue


