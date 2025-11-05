from APP.Core.fidc_selenium_integration import SeleniumIntegration
from APP.DTO.FIDC_DTO import LoginDTO
from APP.Core.fidc_excel_integration import mapear_emps_para_nfs
from time import sleep
from APP.Core.fidc_logic import fazer_pesquisa_com_autocomplete, processar_nfs_inteligente
import logging
from APP.Interfaces.automation_interface import AutomationCommand

# Configurar logger
logger = logging.getLogger(__name__)

class FIDCAutomation(AutomationCommand):
    def __init__(self):
        self.logger = logger
    
    def validate_parameters(self, parameters):
        """Valida se os parâmetros necessários estão presentes"""
        required_params = ['arquivo_excel', 'lojas']
        for param in required_params:
            if param not in parameters:
                self.logger.error(f"Parâmetro obrigatório faltando: {param}")
                return False
        return True
    
    def execute(self, parameters):
        """Executa a automação FIDC com arquivo dinâmico"""
        arquivo_excel = parameters.get('arquivo_excel')
        lojas = parameters.get('lojas')
        
        self.logger.info("📊 INICIANDO AUTOMAÇÃO FIDC")
        self.logger.info(f"📁 Arquivo: {arquivo_excel}")
        self.logger.info(f"🏪 Lojas: {lojas}")
        
        try:
            # Carregar dados do Excel do arquivo recebido
            SHEET = "FIDC Contas a pagar."
            
            self.logger.info("📊 CARREGANDO DADOS DO EXCEL...")
            mapa = mapear_emps_para_nfs(arquivo_excel, SHEET)
            self.logger.info(f"✅ Dados carregados: {len(mapa)} empresas mapeadas")
            
            bot = SeleniumIntegration(timeout=40)
            
            try:
                # 1) Login
                self.logger.info("🔐 FAZENDO LOGIN...")
                bot.login(LoginDTO(
                    usuario="42549981391", 
                    senha="cariri1627"
                ), url="https://web.accesstage.com.br/santander-montadoras-ui/#/login")
                sleep(3)
                
                # 2) Navegação
                self.logger.info("📂 ACESSANDO MÓDULO FIDC...")
                bot.clica_no_modulo_fidc(text_hint="Módulo FIDC")
                bot.clica_em_aberto()
                sleep(3)
                
                self.logger.info(f"🔗 Página atual: {bot.driver.current_url}")
                
                # 3) IDENTIFICAR TABELA
                self.logger.info("🔍 CONFIGURANDO TABELA...")
                self.logger.info("✅ Usando tabela índice: 0 (Títulos Em Aberto)")
                
                resultados_empresas = {}
                
                # Processar cada loja especificada
                for emp in lojas:
                    if emp in mapa:
                        nfs_excel = mapa[emp]
                        self.logger.info(f"\n🏢 PROCESSANDO EMPRESA: {emp}")
                        self.logger.info(f"📋 NFs do Excel: {nfs_excel}")
                        
                        # 4) FAZER PESQUISA
                        self.logger.info("🔄 INICIANDO PESQUISA...")
                        resultado_pesquisa = fazer_pesquisa_com_autocomplete(bot)
                        if not resultado_pesquisa.get('sucesso'):
                            self.logger.error(f"❌ Falha na pesquisa: {resultado_pesquisa.get('motivo')}")
                            resultados_empresas[emp] = {
                                "status": "erro",
                                "motivo": resultado_pesquisa.get('motivo')
                            }
                            continue
                        
                        # 5) PROCESSAR NFs
                        nfs_marcadas, nfs_nao_encontradas, nfs_com_problema = processar_nfs_inteligente(bot, nfs_excel)
                        
                        # Calcular eficiência
                        eficiencia = (nfs_marcadas / len(nfs_excel)) * 100 if nfs_excel else 0
                        
                        resultado_empresa = {
                            "nfs_excel": len(nfs_excel),
                            "nfs_marcadas": nfs_marcadas,
                            "nfs_nao_encontradas": nfs_nao_encontradas,
                            "nfs_com_problema": nfs_com_problema,
                            "eficiencia": eficiencia,
                            "status": "success"
                        }
                        
                        resultados_empresas[emp] = resultado_empresa
                        
                        # Log do resultado da empresa
                        self.logger.info(f"🎯 RESULTADO {emp}:")
                        self.logger.info(f"   • NFs do Excel: {len(nfs_excel)}")
                        self.logger.info(f"   • NFs marcadas: {nfs_marcadas}")
                        self.logger.info(f"   • NFs não encontradas: {len(nfs_nao_encontradas)}")
                        self.logger.info(f"   • NFs com problema: {len(nfs_com_problema)}")
                        self.logger.info(f"   • Eficiência: {eficiencia:.1f}%")
                        
                    else:
                        self.logger.warning(f"⚠️ Empresa {emp} não encontrada no Excel")
                        resultados_empresas[emp] = {
                            "status": "erro", 
                            "motivo": "Empresa não encontrada no Excel"
                        }
                
                # Resultado final consolidado
                resultado_final = {
                    "empresas_processadas": resultados_empresas,
                    "total_empresas": len(lojas),
                    "empresas_com_sucesso": sum(1 for r in resultados_empresas.values() if r.get('status') == 'success'),
                    "status": "completed"
                }
                
                self.logger.info("🎉 PROCESSO CONCLUÍDO!")
                return resultado_final
                
            except Exception as e:
                self.logger.error(f"❌ ERRO durante execução: {e}")
                self.logger.debug("Detalhes do erro:", exc_info=True)
                raise
                
            finally:
                bot.close()
                
        except Exception as e:
            self.logger.error(f"❌ ERRO CRÍTICO: {e}")
            raise