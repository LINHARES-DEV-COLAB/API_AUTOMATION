# fidc_service.py - VERSÃO CORRIGIDA COM LOOP POR EMPRESA

from APP.Core.fidc_selenium_integration import SeleniumIntegration
from APP.DTO.FIDC_DTO import LoginDTO
from APP.Core.fidc_excel_integration import mapear_emps_para_nfs
from time import sleep
from APP.Core.fidc_logic import fazer_pesquisa_com_autocomplete, processar_nfs_com_limite_valor
import logging
import tempfile
import os
from APP.Config.fidc_trata_emp import TrataEmpresa

# Configurar logger
logger = logging.getLogger(__name__)

class FIDCAutomation:
    def __init__(self):
        self.logger = logger
    
    def validate_parameters(self, parameters):
        """Valida se os parâmetros necessários estão presentes"""
        if 'arquivo_excel' not in parameters:
            self.logger.error("Parâmetro obrigatório faltando: arquivo_excel")
            return False
        return True

    def _processar_arquivo_excel(self, arquivo_excel):
        """Processa o arquivo Excel recebido via upload"""
        try:
            # Sheet fixo
            SHEET = "FIDC Contas a pagar."
            
            # Se arquivo_excel é FileStorage do Flask, salva temporariamente
            if hasattr(arquivo_excel, 'read'):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                    arquivo_excel.save(tmp.name)
                    temp_path = tmp.name
                
                try:
                    # Carrega o mapeamento do arquivo temporário
                    mapa = mapear_emps_para_nfs(temp_path, SHEET)
                    self.logger.info(f"✅ Dados carregados: {len(mapa)} empresas mapeadas")
                    return mapa
                finally:
                    # Remove arquivo temporário
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
            else:
                # Se já for um caminho de arquivo (para compatibilidade)
                mapa = mapear_emps_para_nfs(arquivo_excel, SHEET)
                self.logger.info(f"✅ Dados carregados: {len(mapa)} empresas mapeadas")
                return mapa
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar arquivo Excel: {str(e)}")
            raise

    def _fazer_login_empresa(self, bot, emp):
        """Faz login específico para cada empresa"""
        try:
            self.logger.info(f"🔐 FAZENDO LOGIN PARA: {emp}")
            
            # Busca credenciais específicas da empresa
            login_info = TrataEmpresa.trataEmp(emp)
            
            if not login_info or not hasattr(login_info, 'login'):
                self.logger.error(f"❌ Credenciais não encontradas para empresa: {emp}")
                return False
            
            # Faz login com as credenciais da empresa
            bot.login(LoginDTO(
                usuario=login_info.login, 
                senha=login_info.senha
            ), url="https://web.accesstage.com.br/santander-montadoras-ui/#/login")
            
            sleep(3)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro no login para {emp}: {e}")
            return False

    def _navegar_para_modulo_fidc(self, bot):
        """Navega para o módulo FIDC - função reutilizável"""
        try:
            self.logger.info("📂 ACESSANDO MÓDULO FIDC...")
            bot.clica_no_modulo_fidc(text_hint="Módulo FIDC")
            bot.clica_em_aberto()
            sleep(3)
            
            self.logger.info(f"🔗 Página atual: {bot.driver.current_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro na navegação do FIDC: {e}")
            return False

# NO fidc_service.py, na função _processar_empresa, substitua completamente:

    def _processar_empresa(self, bot, emp, nfs_excel):
        """Processa completamente UMA empresa"""
        try:
            self.logger.info(f"\n🏢 INICIANDO PROCESSAMENTO: {emp}")
            self.logger.info(f"📋 NFs para processar: {len(nfs_excel)}")
            
            # FAZER PESQUISA DA EMPRESA
            self.logger.info(f"🔍 FAZENDO PESQUISA PARA: {emp}")
            resultado_pesquisa = fazer_pesquisa_com_autocomplete(bot, emp)
            
            if not resultado_pesquisa.get('sucesso'):
                motivo = resultado_pesquisa.get('motivo', 'Motivo desconhecido')
                self.logger.error(f"❌ Falha na pesquisa: {motivo}")
                return {
                    "status": "erro_pesquisa",
                    "motivo": motivo,
                    "nfs_excel": len(nfs_excel),
                    "boletos_gerados": 0,
                    "nfs_processadas": 0,
                    "nfs_nao_encontradas": nfs_excel,
                    "nfs_com_problema": [],
                    "batches": [],
                    "eficiencia": 0.0
                }
            
            # PROCESSAR NFs COM LIMITE DE VALOR (NOVA LÓGICA)
            self.logger.info(f"🎯 PROCESSANDO {len(nfs_excel)} NFs COM LIMITE DE R$ 250.000...")
            resultados_processamento = processar_nfs_com_limite_valor(bot, nfs_excel, limite_valor=250000)
            
            # Calcular resultados
            eficiencia = (resultados_processamento['nfs_processadas'] / len(nfs_excel)) * 100 if nfs_excel else 0
            
            resultado = {
                "status": "success",
                "nfs_excel": len(nfs_excel),
                "boletos_gerados": resultados_processamento['boletos_gerados'],
                "nfs_processadas": resultados_processamento['nfs_processadas'],
                "nfs_nao_encontradas": resultados_processamento['nfs_nao_encontradas'],
                "nfs_com_problema": resultados_processamento['nfs_com_problema'],
                "batches": resultados_processamento['batches'],
                "eficiencia": eficiencia
            }
            
            self.logger.info(f"✅ FINALIZADO {emp}:")
            self.logger.info(f"   • Boletos gerados: {resultados_processamento['boletos_gerados']}")
            self.logger.info(f"   • NFs processadas: {resultados_processamento['nfs_processadas']}/{len(nfs_excel)}")
            self.logger.info(f"   • Eficiência: {eficiencia:.1f}%")
            
            return resultado
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar empresa {emp}: {e}")
            return {
                "status": "erro_processamento", 
                "motivo": str(e),
                "nfs_excel": len(nfs_excel),
                "boletos_gerados": 0,
                "nfs_processadas": 0,
                "nfs_nao_encontradas": nfs_excel,
                "nfs_com_problema": [],
                "batches": [],
                "eficiencia": 0.0
            }
    def execute(self, parameters):
        """Executa a automação FIDC com loop por TODAS as empresas"""
        arquivo_excel = parameters.get('arquivo_excel')
        lojas_param = parameters.get('lojas')
        
        self.logger.info("📊 INICIANDO AUTOMAÇÃO FIDC - LOOP POR EMPRESAS")
        self.logger.info(f"📁 Arquivo: {arquivo_excel.filename if hasattr(arquivo_excel, 'filename') else 'Arquivo'}")
        
        try:
            # Carregar dados do Excel
            self.logger.info("📊 CARREGANDO DADOS DO EXCEL...")
            mapa = self._processar_arquivo_excel(arquivo_excel)
            
            # Determinar quais empresas processar
            if lojas_param and isinstance(lojas_param, list) and lojas_param:
                lojas = [emp for emp in lojas_param if emp in mapa]
                self.logger.info(f"🏪 Processando empresas específicas: {lojas}")
            else:
                # PEGAR TODAS AS EMPRESAS DO EXCEL
                lojas = list(mapa.keys())
                self.logger.info(f"🏪 Processando automaticamente TODAS as {len(lojas)} empresas do Excel")
            
            if not lojas:
                self.logger.warning("⚠️ Nenhuma empresa encontrada para processar")
                return {
                    "empresas_processadas": {},
                    "total_empresas": 0,
                    "empresas_com_sucesso": 0,
                    "status": "no_data",
                    "mensagem": "Nenhuma empresa encontrada no arquivo Excel"
                }
            
            # Inicializar driver Selenium
            bot = SeleniumIntegration(timeout=40)
            resultados_empresas = {}
            
            try:
                # LOOP PRINCIPAL - UMA EMPRESA POR VEZ
                for i, emp in enumerate(lojas, 1):
                    self.logger.info(f"\n{'='*60}")
                    self.logger.info(f"🚀 INICIANDO EMPRESA {i}/{len(lojas)}: {emp}")
                    self.logger.info(f"{'='*60}")
                    
                    nfs_excel = mapa[emp]
                    
                    # 1) LOGIN ESPECÍFICO DA EMPRESA
                    if not self._fazer_login_empresa(bot, emp):
                        resultados_empresas[emp] = {
                            "status": "erro_login",
                            "nfs_excel": len(nfs_excel),
                            "nfs_marcadas": 0,
                            "nfs_nao_encontradas": nfs_excel,
                            "nfs_com_problema": [],
                            "eficiencia": 0.0
                        }
                        continue
                    
                    # 2) NAVEGAÇÃO PARA MÓDULO FIDC
                    if not self._navegar_para_modulo_fidc(bot):
                        resultados_empresas[emp] = {
                            "status": "erro_navegacao",
                            "nfs_excel": len(nfs_excel),
                            "nfs_marcadas": 0,
                            "nfs_nao_encontradas": nfs_excel,
                            "nfs_com_problema": [],
                            "eficiencia": 0.0
                        }
                        continue
                    
                    # 3) PROCESSAMENTO COMPLETO DA EMPRESA
                    resultado_empresa = self._processar_empresa(bot, emp, nfs_excel)
                    resultados_empresas[emp] = resultado_empresa
                    
                    # 4) LOGOUT IMPLÍCITO - próximo login será de outra empresa
                    self.logger.info(f"✅ FINALIZADO PROCESSAMENTO DE: {emp}")
                    
                    # Pequena pausa entre empresas
                    if i < len(lojas):
                        self.logger.info("⏳ Aguardando 2 segundos antes da próxima empresa...")
                        sleep(2)
                
                # RESULTADO FINAL CONSOLIDADO
# NO fidc_service.py, na função execute, atualize o resultado final:

# RESULTADO FINAL CONSOLIDADO
                    resultado_final = {
                        "empresas_processadas": resultados_empresas,
                        "total_empresas": len(lojas),
                        "empresas_com_sucesso": sum(1 for r in resultados_empresas.values() if r.get('status') == 'success'),
                        "empresas_com_erro": sum(1 for r in resultados_empresas.values() if r.get('status') != 'success'),
                        "total_nfs_excel": sum(r.get('nfs_excel', 0) for r in resultados_empresas.values()),
                        "total_nfs_processadas": sum(r.get('nfs_processadas', 0) for r in resultados_empresas.values()),
                        "total_boletos_gerados": sum(r.get('boletos_gerados', 0) for r in resultados_empresas.values()),
                        "status": "completed"
                    }

                    # Calcular eficiência geral
                    if resultado_final['total_nfs_excel'] > 0:
                        resultado_final['eficiencia_geral'] = (resultado_final['total_nfs_processadas'] / resultado_final['total_nfs_excel']) * 100
                    else:
                        resultado_final['eficiencia_geral'] = 0

                    self.logger.info("🎉 PROCESSO CONCLUÍDO!")
                    self.logger.info(f"📊 RESUMO FINAL:")
                    self.logger.info(f"   • Empresas processadas: {resultado_final['total_empresas']}")
                    self.logger.info(f"   • Empresas com sucesso: {resultado_final['empresas_com_sucesso']}")
                    self.logger.info(f"   • Empresas com erro: {resultado_final['empresas_com_erro']}")
                    self.logger.info(f"   • Total NFs Excel: {resultado_final['total_nfs_excel']}")
                    self.logger.info(f"   • Total NFs Processadas: {resultado_final['total_nfs_processadas']}")
                    self.logger.info(f"   • Total Boletos Gerados: {resultado_final['total_boletos_gerados']}")
                    self.logger.info(f"   • Eficiência Geral: {resultado_final['eficiencia_geral']:.1f}%")
                                    
                return resultado_final
                
            except Exception as e:
                self.logger.error(f"❌ ERRO durante execução: {e}")
                raise
                
            finally:
                bot.close()
                
        except Exception as e:
            self.logger.error(f"❌ ERRO CRÍTICO: {e}")
            raise

    def test_connection(self, emp):
        """Testa a conexão com o sistema FIDC"""
        try:
            bot = SeleniumIntegration(timeout=20)
            login_info = TrataEmpresa.trataEmp(emp)
            
            if not login_info:
                return {"status": "error", "message": f"Empresa {emp} não encontrada"}
            
            bot.login(LoginDTO(
                usuario=login_info.login, 
                senha=login_info.senha
            ), url="https://web.accesstage.com.br/santander-montadoras-ui/#/login")
            
            sleep(2)
            bot.close()
            return {"status": "success", "message": f"Conexão testada com sucesso para {emp}"}
            
        except Exception as e:
            return {"status": "error", "message": f"Falha na conexão para {emp}: {str(e)}"}