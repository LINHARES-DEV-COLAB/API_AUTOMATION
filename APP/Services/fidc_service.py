from APP.Services.fidc_selenium_integration import SeleniumIntegration
from APP.DTO.FIDC_DTO import LoginDTO
from APP.Services.fidc_excel_integration import mapear_emps_para_nfs
from APP.Config.fidc_trata_emp import trataEmp
from time import sleep

XLSX = r"C:\Users\sousa.lima\Documents\Projetos\EmissaoBoletoFIDC\app\data\FIDC CAP DIARIO.xlsx"
SHEET = "FIDC Contas a pagar."

def run():
    # 1) mapa EMP -> [NFs...]
    mapa = mapear_emps_para_nfs(XLSX, SHEET)
    
    bot = SeleniumIntegration(timeout=25)
    try:
        url = "https://web.accesstage.com.br/santander-montadoras-ui/#/login"

        bot.login(LoginDTO(
            usuario="42549981391",
            senha="cariri1627"), url=url
        )
        
        sleep(2)  # Aguarda menu abrir
        
        print("=== FASE 1: DIAGNÓSTICO ===")
        bot.clica_no_modulo_fidc(text_hint="Módulo FIDC")

        bot.clica_em_aberto()
        
        relatorio = {}

        for emp, nfs in mapa.items():
            if emp != "TA" or not nfs:
                continue

            termo = trataEmp(emp)
            bot.insere_revenda(termo=termo, texto_completo=None)
            bot.clica_em_pesquisa()

            resultados = bot.marcar_nfs_do_emp(nfs)  # {nf: True/False}
            relatorio[emp] = resultados

        ok_total = sum(sum(1 for v in r.values() if v) for r in relatorio.values())
        falhas_total = sum(sum(1 for v in r.values() if not v) for r in relatorio.values())
        print(f"Concluído. Marcados: {ok_total} | Não encontrados: {falhas_total}")

        # Opcional: logar quais NFs não foram encontradas
        for emp, r in relatorio.items():
            faltantes = [nf for nf, ok in r.items() if not ok]
            if faltantes:
                print(f"[{emp}] NFs não encontradas: {', '.join(faltantes)}")

    except Exception as e:
        print(f"Erro ocorreu: {e}")
    finally:
         bot.close()

if __name__ == "__main__":
    run()