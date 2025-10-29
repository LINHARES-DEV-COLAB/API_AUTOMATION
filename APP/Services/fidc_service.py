from APP.Core.fidc_selenium_integration import SeleniumIntegration
from APP.DTO.FIDC_DTO import LoginDTO
from APP.Core.fidc_excel_integration import mapear_emps_para_nfs
from time import sleep
from APP.Core.fidc_logic import fazer_pesquisa_com_autocomplete, processar_nfs_inteligente

def run():
    # Carregar dados do Excel
    XLSX = r"C:\Users\sousa.lima\Documents\Projetos\ApiAutomation\API_AUTOMATION\APP\Data\FIDC CAP DIARIO.xlsx"
    SHEET = "FIDC Contas a pagar."
    
    print("📊 CARREGANDO DADOS DO EXCEL...")
    mapa = mapear_emps_para_nfs(XLSX, SHEET)
    
    bot = SeleniumIntegration(timeout=40)
    
    try:
        # 1) Login
        print("\n🔐 FAZENDO LOGIN...")
        bot.login(LoginDTO(
            usuario="42549981391", 
            senha="cariri1627"
        ), url="https://web.accesstage.com.br/santander-montadoras-ui/#/login")
        sleep(3)
        
        # 2) Navegação
        print("📂 ACESSANDO MÓDULO FIDC...")
        bot.clica_no_modulo_fidc(text_hint="Módulo FIDC")
        bot.clica_em_aberto()
        sleep(3)
        
        print(f"🔗 Página atual: {bot.driver.current_url}")
        
        # 3) IDENTIFICAR TABELA
        print("\n🔍 CONFIGURANDO TABELA...")
        print("   ✅ Usando tabela índice: 0 (Títulos Em Aberto)")
        
        emp = "TA"
        if emp in mapa:
            nfs_excel = mapa[emp]
            print(f"\n🏢 EMPRESA: {emp}")
            print(f"   📋 NFs do Excel: {nfs_excel}")
            
            # 4) FAZER PESQUISA
            print("🔄 INICIANDO PESQUISA...")
            resultado_pesquisa = fazer_pesquisa_com_autocomplete(bot)
            if not resultado_pesquisa.get('sucesso'):
                print(f"❌ Falha na pesquisa: {resultado_pesquisa.get('motivo')}")
                return
            
            # 5) PROCESSAR NFs
            nfs_marcadas, nfs_nao_encontradas, nfs_com_problema = processar_nfs_inteligente(bot, nfs_excel)
            
            # 6) RELATÓRIO FINAL
            print(f"\n🎉 RELATÓRIO FINAL")
            print("=" * 50)
            print(f"📊 RESULTADOS:")
            print(f"   • NFs do Excel: {len(nfs_excel)}")
            print(f"   • NFs marcadas: {nfs_marcadas}")
            print(f"   • NFs não encontradas: {len(nfs_nao_encontradas)}")
            print(f"   • NFs com problema: {len(nfs_com_problema)}")
            
            if nfs_nao_encontradas:
                print(f"\n📋 NFs NÃO ENCONTRADAS:")
                for nf in nfs_nao_encontradas:
                    print(f"   • {nf}")
            
            if nfs_com_problema:
                print(f"\n⚠️  NFs COM PROBLEMA:")
                for nf, motivo in nfs_com_problema:
                    print(f"   • {nf} - {motivo}")
            
            eficiencia = (nfs_marcadas / len(nfs_excel)) * 100 if nfs_excel else 0
            print(f"\n💡 EFICIÊNCIA: {eficiencia:.1f}%")
            
            if nfs_marcadas == len(nfs_excel):
                print("   🎉 TODAS as NFs do Excel foram marcadas!")
            elif nfs_marcadas > 0:
                print(f"   ✅ {nfs_marcadas} NFs marcadas com sucesso")
            else:
                print("   ❌ Nenhuma NF do Excel foi encontrada")
        
        print(f"\n🎉 PROCESSO CONCLUÍDO!")
        
        print("\n🔍 Browser mantido aberto para verificação...")
        input("⏸️  Pressione Enter para fechar...")
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n🔍 Browser mantido aberto para debug...")
        input("⏸️  Pressione Enter para fechar...")
    finally:


        bot.close()

if __name__ == "__main__":
    run()