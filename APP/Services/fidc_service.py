# fidc_service.py - VERSÃO CORRIGIDA COM DOWNLOAD DE BOLETOS

import os
import tempfile
import logging
from datetime import datetime
from time import sleep
from selenium.webdriver.common.by import By  # IMPORT ADICIONADO
from APP.Core.fidc_selenium_integration import SeleniumIntegration
from APP.DTO.FIDC_DTO import LoginDTO
from APP.Core.fidc_excel_integration import mapear_emps_para_nfs
from APP.Core.fidc_logic import fazer_pesquisa_com_autocomplete, processar_nfs_com_limite_valor
from APP.Config.fidc_trata_emp import TrataEmpresa

logger = logging.getLogger(__name__)

class FIDCAutomation:
    def __init__(self):
        self.logger = logger
        self.download_dir = None
    
    def validate_parameters(self, parameters):
        """Valida se os parâmetros necessários estão presentes"""
        if 'arquivo_excel' not in parameters:
            self.logger.error("Parâmetro obrigatório faltando: arquivo_excel")
            return False
        return True

    def _processar_arquivo_excel(self, arquivo_excel):
        """Processa o arquivo Excel recebido via upload"""
        try:
            SHEET = "FIDC Contas a pagar."
            
            if hasattr(arquivo_excel, 'read'):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                    arquivo_excel.save(tmp.name)
                    temp_path = tmp.name
                
                try:
                    mapa = mapear_emps_para_nfs(temp_path, SHEET)
                    self.logger.info(f"✅ Dados carregados: {len(mapa)} empresas mapeadas")
                    return mapa
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
            else:
                mapa = mapear_emps_para_nfs(arquivo_excel, SHEET)
                self.logger.info(f"✅ Dados carregados: {len(mapa)} empresas mapeadas")
                return mapa
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar arquivo Excel: {str(e)}")
            raise

    def _setup_download_directory(self):
        """Configura diretório temporário para downloads"""
        self.download_dir = tempfile.mkdtemp()
        self.logger.info(f"📁 Diretório de download: {self.download_dir}")
        return self.download_dir

    def _fazer_login_empresa(self, bot, emp):
        """Faz login específico para cada empresa"""
        try:
            self.logger.info(f"🔐 FAZENDO LOGIN PARA: {emp}")
            
            login_info = TrataEmpresa.trataEmp(emp)
            
            if not login_info or not hasattr(login_info, 'login'):
                self.logger.error(f"❌ Credenciais não encontradas para empresa: {emp}")
                return False
            
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
        """Navega para o módulo FIDC"""
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

    def _get_pdf_download_button(self, bot, emp, nf_number):
        """Localiza o botão de download do PDF"""
        try:
            sleep(2)
            
            # XPath para botões de PDF em Agrupamentos de Boletos
            xpath_agrupados = "//mat-expansion-panel[contains(., 'Agrupamentos de Boletos')]//button[contains(@mattooltip, 'PDF')]"
            
            # XPath para botões de PDF em Títulos Em Aberto (não desabilitados)
            xpath_individual = "//mat-expansion-panel[contains(., 'Titulos Em Aberto')]//button[contains(@mattooltip, 'PDF') and not(@disabled)]"
            
            # Primeiro tenta os agrupados
            elementos_agrupados = bot.driver.find_elements(By.XPATH, xpath_agrupados)
            if elementos_agrupados:
                self.logger.info(f"📄 Encontrado {len(elementos_agrupados)} botão(ões) de PDF em Agrupamentos")
                return elementos_agrupados[0]
            
            # Tenta os individuais
            elementos_individuais = bot.driver.find_elements(By.XPATH, xpath_individual)
            if elementos_individuais:
                self.logger.info(f"📄 Encontrado {len(elementos_individuais)} botão(ões) de PDF individuais")
                return elementos_individuais[0]
            
            self.logger.warning("❌ Nenhum botão de PDF encontrado")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao buscar botão de PDF: {e}")
            return None

    def _download_boleto(self, bot, emp, nf_number, download_dir):
        """Faz o download do boleto PDF"""
        try:
            botao_pdf = self._get_pdf_download_button(bot, emp, nf_number)
            if not botao_pdf:
                return None
            
            # Nome do arquivo baseado na empresa e data
            data_hoje = datetime.now().strftime("%Y%m%d")
            nome_empresa_limpo = "".join(c for c in emp if c.isalnum() or c in (' ', '-', '_')).rstrip()
            nome_arquivo = f"Boleto_{nome_empresa_limpo}_{nf_number}_{data_hoje}.pdf"
            caminho_completo = os.path.join(download_dir, nome_arquivo)
            
            self.logger.info(f"💾 Tentando download: {nome_arquivo}")
            
            # Clica no botão de PDF
            bot.driver.execute_script("arguments[0].click();", botao_pdf)
            sleep(5)  # Aguarda o download
            
            # Verifica se o arquivo foi baixado
            arquivos_baixados = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
            
            if arquivos_baixados:
                # Encontra o arquivo mais recente
                arquivo_mais_recente = max(
                    [os.path.join(download_dir, f) for f in arquivos_baixados],
                    key=os.path.getctime
                )
                
                # Renomeia o arquivo
                if arquivo_mais_recente != caminho_completo:
                    if os.path.exists(caminho_completo):
                        os.remove(caminho_completo)
                    os.rename(arquivo_mais_recente, caminho_completo)
                
                self.logger.info(f"✅ Download realizado: {nome_arquivo}")
                return caminho_completo
            else:
                self.logger.warning("⚠️ Nenhum arquivo PDF foi baixado")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Erro no download do boleto: {e}")
            return None

    def _processar_empresa_com_download(self, bot, emp, nfs_excel, download_dir):
        """Processa empresa incluindo download de boletos"""
        try:
            self.logger.info(f"\n🏢 INICIANDO PROCESSAMENTO COM DOWNLOAD: {emp}")
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
                    "boletos_baixados": 0,
                    "nfs_processadas": 0,
                    "nfs_nao_encontradas": nfs_excel,
                    "nfs_com_problema": [],
                    "batches": [],
                    "eficiencia": 0.0,
                    "arquivos_baixados": []
                }
            
            # PROCESSAR NFs
            self.logger.info(f"🎯 PROCESSANDO {len(nfs_excel)} NFs COM LIMITE DE R$ 250.000...")
            resultados_processamento = processar_nfs_com_limite_valor(bot, nfs_excel, limite_valor=250000)
            
            # TENTAR BAIXAR BOLETOS GERADOS
            arquivos_baixados = []
            boletos_baixados = 0
            
            if resultados_processamento['boletos_gerados'] > 0:
                self.logger.info(f"📥 Tentando baixar {resultados_processamento['boletos_gerados']} boleto(s)")
                
                # Para cada NF processada, tenta baixar o boleto
                for batch in resultados_processamento.get('batches', []):
                    for nf in batch.get('nfs_processadas', []):
                        if isinstance(nf, dict) and 'numero' in nf:
                            nf_numero = nf['numero']
                        else:
                            nf_numero = str(nf)
                            
                        caminho_arquivo = self._download_boleto(bot, emp, nf_numero, download_dir)
                        if caminho_arquivo:
                            arquivos_baixados.append(caminho_arquivo)
                            boletos_baixados += 1
                            sleep(2)  # Pausa entre downloads
            
            # Calcular resultados
            eficiencia = (resultados_processamento['nfs_processadas'] / len(nfs_excel)) * 100 if nfs_excel else 0
            
            resultado = {
                "status": "success",
                "nfs_excel": len(nfs_excel),
                "boletos_gerados": resultados_processamento['boletos_gerados'],
                "boletos_baixados": boletos_baixados,
                "nfs_processadas": resultados_processamento['nfs_processadas'],
                "nfs_nao_encontradas": resultados_processamento['nfs_nao_encontradas'],
                "nfs_com_problema": resultados_processamento['nfs_com_problema'],
                "batches": resultados_processamento['batches'],
                "eficiencia": eficiencia,
                "arquivos_baixados": arquivos_baixados
            }
            
            self.logger.info(f"✅ FINALIZADO {emp}:")
            self.logger.info(f"   • Boletos gerados: {resultados_processamento['boletos_gerados']}")
            self.logger.info(f"   • Boletos baixados: {boletos_baixados}")
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
                "boletos_baixados": 0,
                "nfs_processadas": 0,
                "nfs_nao_encontradas": nfs_excel,
                "nfs_com_problema": [],
                "batches": [],
                "eficiencia": 0.0,
                "arquivos_baixados": []
            }

    def execute(self, parameters):
        """Executa a automação FIDC com download de boletos"""
        arquivo_excel = parameters.get('arquivo_excel')
        lojas_param = parameters.get('lojas')
        
        self.logger.info("📊 INICIANDO AUTOMAÇÃO FIDC - COM DOWNLOAD DE BOLETOS")
        self.logger.info(f"📁 Arquivo: {arquivo_excel.filename if hasattr(arquivo_excel, 'filename') else 'Arquivo'}")
        
        try:
            # Configurar diretório de download
            download_dir = self._setup_download_directory()
            
            # Carregar dados do Excel
            self.logger.info("📊 CARREGANDO DADOS DO EXCEL...")
            mapa = self._processar_arquivo_excel(arquivo_excel)
            
            # Determinar empresas para processar
            if lojas_param and isinstance(lojas_param, list) and lojas_param:
                lojas = [emp for emp in lojas_param if emp in mapa]
                self.logger.info(f"🏪 Processando empresas específicas: {lojas}")
            else:
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
            
            # Configurar download se for Chrome
            if hasattr(bot, 'driver') and 'chrome' in bot.driver.name.lower():
                if hasattr(bot, 'configure_download'):
                    bot.configure_download(download_dir)
                else:
                    self.logger.warning("⚠️ Método configure_download não disponível no SeleniumIntegration")
            
            resultados_empresas = {}
            todos_arquivos_baixados = []
            
            try:
                # LOOP PRINCIPAL POR EMPRESAS
                for i, emp in enumerate(lojas, 1):
                    self.logger.info(f"\n{'='*60}")
                    self.logger.info(f"🚀 EMPRESA {i}/{len(lojas)}: {emp}")
                    self.logger.info(f"{'='*60}")
                    
                    nfs_excel = mapa[emp]
                    
                    # 1) LOGIN
                    if not self._fazer_login_empresa(bot, emp):
                        resultados_empresas[emp] = {
                            "status": "erro_login",
                            "nfs_excel": len(nfs_excel),
                            "boletos_baixados": 0,
                            "arquivos_baixados": []
                        }
                        continue
                    
                    # 2) NAVEGAÇÃO FIDC
                    if not self._navegar_para_modulo_fidc(bot):
                        resultados_empresas[emp] = {
                            "status": "erro_navegacao",
                            "nfs_excel": len(nfs_excel),
                            "boletos_baixados": 0,
                            "arquivos_baixados": []
                        }
                        continue
                    
                    # 3) PROCESSAMENTO COM DOWNLOAD
                    resultado_empresa = self._processar_empresa_com_download(bot, emp, nfs_excel, download_dir)
                    resultados_empresas[emp] = resultado_empresa
                    todos_arquivos_baixados.extend(resultado_empresa.get('arquivos_baixados', []))
                    
                    self.logger.info(f"✅ FINALIZADO PROCESSAMENTO DE: {emp}")
                    
                    # Pausa entre empresas
                    if i < len(lojas):
                        self.logger.info("⏳ Aguardando 2 segundos antes da próxima empresa...")
                        sleep(2)
                
                # RESULTADO FINAL CONSOLIDADO
                resultado_final = {
                    "empresas_processadas": resultados_empresas,
                    "total_empresas": len(lojas),
                    "empresas_com_sucesso": sum(1 for r in resultados_empresas.values() if r.get('status') == 'success'),
                    "empresas_com_erro": sum(1 for r in resultados_empresas.values() if r.get('status') != 'success'),
                    "total_nfs_excel": sum(r.get('nfs_excel', 0) for r in resultados_empresas.values()),
                    "total_nfs_processadas": sum(r.get('nfs_processadas', 0) for r in resultados_empresas.values()),
                    "total_boletos_gerados": sum(r.get('boletos_gerados', 0) for r in resultados_empresas.values()),
                    "total_boletos_baixados": sum(r.get('boletos_baixados', 0) for r in resultados_empresas.values()),
                    "total_arquivos_baixados": len(todos_arquivos_baixados),
                    "diretorio_download": download_dir,
                    "arquivos_baixados": todos_arquivos_baixados,
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
                self.logger.info(f"   • Total NFs Excel: {resultado_final['total_nfs_excel']}")
                self.logger.info(f"   • Total NFs Processadas: {resultado_final['total_nfs_processadas']}")
                self.logger.info(f"   • Total Boletos Baixados: {resultado_final['total_boletos_baixados']}")
                self.logger.info(f"   • Eficiência Geral: {resultado_final['eficiencia_geral']:.1f}%")
                self.logger.info(f"   • Arquivos em: {download_dir}")
                
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