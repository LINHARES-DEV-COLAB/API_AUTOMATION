# APP/Services/pan_service.py - VERSÃO COMPLETA E IMPLEMENTADA
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import re
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import oracledb
import os

from APP.protected_resource import ProtectedResource

logger = logging.getLogger(__name__)

@dataclass
class ResultadoPan:
    titulo: str
    duplicata: str
    valor: float
    
    def to_dict(self):
        return {
            "TITULO": self.titulo,
            "DUPLICATA": self.duplicata,
            "VALOR": f"{self.valor:.2f}".replace('.', ',')
        }

class PanAutomation:
    def __init__(self):
        self.base_dir_rede = r"\\172.17.67.14\Ares Motos\controladoria\financeiro\06.CONTAS A RECEBER\11.RELATÓRIOS BANCO PAN"
        print("✅ PanService inicializado")
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Valida se os parâmetros necessários estão presentes"""
        print("🔍 Validando parâmetros para PAN...")
        
        required_params = ['arquivo_excel']
        for param in required_params:
            if param not in parameters:
                print(f"❌ Parâmetro obrigatório faltando: {param}")
                return False
        
        # Verifica se o arquivo existe
        arquivo_path = parameters['arquivo_excel']
        if not os.path.exists(arquivo_path):
            print(f"❌ Arquivo não encontrado: {arquivo_path}")
            return False
            
        print("✅ Parâmetros válidos para PAN")
        return True
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Executa a automação PAN com os parâmetros fornecidos"""
        print("🚀 Executando automação PAN...")
        
        try:
            arquivo_excel = parameters.get('arquivo_excel')
            data_param = parameters.get('data')
            
            print(f"📁 Arquivo: {arquivo_excel}")
            print(f"📅 Data: {data_param}")
            
            # Chama o método apropriado baseado na data
            if data_param:
                resultados = self.processar_extrato_com_data(arquivo_excel, data_param)
            else:
                resultados = self.processar_extrato(arquivo_excel)
            
            # Converte resultados para dicionário
            resultados_dict = [resultado.to_dict() for resultado in resultados]
            
            print(f"✅ PAN concluído. {len(resultados_dict)} registros processados")
            
            return {
                "status": "completed",
                "resultados": resultados_dict,
                "total_processado": len(resultados_dict),
                "mensagem": f"Processados {len(resultados_dict)} registros do PAN com sucesso"
            }
            
        except Exception as e:
            print(f"❌ Erro na execução do PAN: {e}")
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Traceback: {error_trace}")
            
            return {
                "status": "error",
                "erro": str(e),
                "traceback": error_trace
            }
    
    def processar_extrato(self, caminho_arquivo: str, data_param: str = None) -> List[ResultadoPan]:
        try:
            print(f"\n" + "="*60)
            print("🔍 INICIANDO PROCESSAMENTO DO EXTRATO PAN")
            if data_param:
                print(f"📅 DATA ENVIADA PELO USUÁRIO: {data_param}")
            print("="*60)
            
            # 1. Upload e leitura do arquivo
            df_extrato = self._ler_extrato_itaú(caminho_arquivo)
            
            # 2. Filtragem de lançamentos relevantes
            valores_pan = self._filtrar_lancamentos_pan(df_extrato)
            
            if not valores_pan:
                print("❌ Nenhum lançamento PAN encontrado no extrato")
                return []
            
            print(f"✅ Valores PAN encontrados: {valores_pan}")
            
            # 3. Busca em diretório de rede
            resultados = []
                
            for valor in valores_pan:
                print(f"\n💰 PROCESSANDO VALOR: R$ {valor:,.2f}")
                
                # Buscar o arquivo correspondente ao valor (PASSANDO A DATA)
                arquivo_encontrado = self._buscar_arquivo_por_valor(valor, data_param)
                
                if arquivo_encontrado:
                    # 4. Extração de informações do relatório
                    chassi = self._extrair_chassi_do_relatorio(arquivo_encontrado, valor)
                    
                    if chassi:
                        print(f"✅ Chassi encontrado: {chassi}")
                        # Consulta no banco de dados
                        resultado_banco = self._consultar_banco_dados(chassi, valor)
                        
                        if resultado_banco:
                            resultados.append(resultado_banco)
                            print(f"✅✅✅ VALOR PROCESSADO COM SUCESSO: R$ {valor:,.2f}")
                            print(f"   📝 Dados: Título {resultado_banco.titulo}, Duplicata {resultado_banco.duplicata}")
                        else:
                            print(f"⚠️  Dados não encontrados no banco para chassi {chassi}")
                    else:
                        print(f"⚠️  Chassi não encontrado no relatório")
                else:
                    print(f"❌ Arquivo não encontrado para o valor R$ {valor:,.2f}")
            
            # DEBUG FINAL
            print(f"\n" + "="*60)
            print("🔍 DEBUG FINAL - TODOS OS RESULTADOS COLETADOS")
            print("="*60)
            print(f"📊 Total de valores PAN no extrato: {len(valores_pan)}")
            print(f"📊 Total de resultados processados: {len(resultados)}")
            
            for i, resultado in enumerate(resultados):
                print(f"   {i+1}. Título: {resultado.titulo}, Duplicata: {resultado.duplicata}, Valor: R$ {resultado.valor:,.2f}")
            
            print(f"📊 RESULTADO FINAL: {len(resultados)} registros processados")
            return resultados
                
        except Exception as e:
            print(f"❌ ERRO NO PROCESSAMENTO: {e}")
            raise
    
    def _ler_extrato_itaú(self, caminho_arquivo: str) -> pd.DataFrame:
        """
        Lê o arquivo de extrato Itaú a partir da linha 10
        """
        try:
            print(f"📁 Lendo arquivo: {caminho_arquivo}")
            
            # Lê a partir da linha 10 (índice 9)
            df = pd.read_excel(caminho_arquivo, header=9)
            
            # Remove linhas totalmente vazias
            df = df.dropna(how='all')
            
            print(f"✅ Arquivo lido: {len(df)} linhas")
            return df
            
        except Exception as e:
            print(f"❌ Erro na leitura do extrato: {e}")
            raise
    
    def _filtrar_lancamentos_pan(self, df_extrato: pd.DataFrame) -> List[float]:
        """
        Filtra linhas onde 'Lançamento' contém 'Pan' e extrai os valores
        """
        try:
            # Encontra a coluna de lançamento
            col_lancamento = None
            for col in df_extrato.columns:
                col_lower = str(col).lower()
                if any(termo in col_lower for termo in ['lançamento', 'lancamento', 'descrição', 'descricao']):
                    col_lancamento = col
                    break
            
            if col_lancamento is None:
                col_lancamento = df_extrato.columns[1]
            
            # Encontra a coluna de valor
            col_valor = None
            for col in df_extrato.columns:
                col_lower = str(col).lower()
                if any(termo in col_lower for termo in ['valor', 'vlr', 'valor (r$)']):
                    col_valor = col
                    break
            
            if col_valor is None:
                col_valor = df_extrato.columns[-1]
            
            # Filtra linhas com 'Pan' no lançamento
            mask_pan = df_extrato[col_lancamento].astype(str).str.contains('pan', case=False, na=False)
            df_pan = df_extrato[mask_pan]
            
            print(f"📊 Lançamentos PAN encontrados: {len(df_pan)}")
            
            # Converte valores para float
            valores = []
            for valor in df_pan[col_valor]:
                try:
                    valor_float = self._converter_valor_para_float(valor)
                    if valor_float is not None:
                        valores.append(round(valor_float, 2))
                except (ValueError, TypeError):
                    continue
            
            # Remove duplicatas e retorna
            valores_unicos = list(set(valores))
            return valores_unicos
            
        except Exception as e:
            print(f"❌ Erro no filtro de lançamentos PAN: {e}")
            return []
    
    def _converter_valor_para_float(self, valor) -> Optional[float]:
        if pd.isna(valor):
            return None
        
        if isinstance(valor, (int, float)):
            return float(valor)
        
        try:
            valor_str = str(valor).strip()
            
            # Se já está vazio, retorna None
            if not valor_str or valor_str.lower() in ['nan', 'none', 'nat']:
                return None
            
            # Remove caracteres não numéricos (exceto ponto, vírgula e sinal)
            valor_str = re.sub(r'[^\d,\-\.]', '', valor_str)
            
            # Se ficou vazio após limpeza, retorna None
            if not valor_str:
                return None
            
            # Detecta formato brasileiro vs americano
            if '.' in valor_str and ',' in valor_str:
                # Formato brasileiro: 1.234,56 - remove pontos, substitui vírgula
                # Verifica se a vírgula é o separador decimal (tem 2 casas depois)
                parts = valor_str.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    valor_str = valor_str.replace('.', '').replace(',', '.')
                else:
                    # Vírgula como separador de milhares
                    valor_str = valor_str.replace(',', '')
            elif ',' in valor_str:
                # Só tem vírgula - verifica se é decimal
                parts = valor_str.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    valor_str = valor_str.replace(',', '.')  # vírgula decimal
                else:
                    valor_str = valor_str.replace(',', '')   # vírgula como milhares
            
            # Converte para float
            return float(valor_str)
        except Exception as e:
            return None
        
    def _buscar_arquivo_por_valor(self, valor: float, data_param: str = None) -> Optional[Path]:
        datas_busca = self._obter_datas_para_busca(data_param)
        
        print(f"   🔍 Buscando arquivo para R$ {valor:,.2f}")
        print(f"   📅 Datas: {datas_busca}")
        
        for data_str in datas_busca:
            pasta_data = Path(self.base_dir_rede) / data_str
            
            if not pasta_data.exists():
                print(f"   ❌ Pasta não existe: {data_str}")
                continue
            
            print(f"   📂 Verificando pasta: {data_str}")
            
            # Busca arquivos Excel na pasta
            arquivos = list(pasta_data.glob("*.xlsx")) + list(pasta_data.glob("*.xls"))
            arquivos = [arq for arq in arquivos if not arq.name.startswith('~$')]
            
            print(f"   📄 Arquivos encontrados: {len(arquivos)}")
            
            for arquivo in arquivos:
                print(f"      🔎 Analisando: {arquivo.name}")
                
                # Verifica se o valor está no nome do arquivo
                if self._valor_no_nome_arquivo(arquivo, valor):
                    print(f"      ✅ ENCONTRADO no nome do arquivo!")
                    return arquivo
                
                # Ou verifica se o valor está no conteúdo do arquivo
                if self._valor_no_conteudo_arquivo(arquivo, valor):
                    print(f"      ✅ ENCONTRADO no conteúdo do arquivo!")
                    return arquivo
                
                print(f"      ❌ Valor não encontrado em {arquivo.name}")
            
            print(f"   ❌ Nenhum arquivo encontrado na data {data_str}")
        
        print(f"   ❌❌❌ NENHUM ARQUIVO ENCONTRADO PARA R$ {valor:,.2f}")
        return None
        
    def _obter_datas_para_busca(self, data_param: str = None) -> List[str]:
        if data_param:
            try:
                data_principal = datetime.strptime(data_param, "%d-%m-%Y")
                datas = [data_principal.strftime("%d-%m-%Y")]
                
                # Adiciona o dia ANTERIOR (para casos em que o pagamento chegou antes)
                dia_anterior = data_principal - timedelta(days=1)
                datas.append(dia_anterior.strftime("%d-%m-%Y"))
                
                # Adiciona o dia SEGUINTE (para casos em que o pagamento chegou depois)
                dia_seguinte = data_principal + timedelta(days=1)
                datas.append(dia_seguinte.strftime("%d-%m-%Y"))
                
                # Se a data principal for sexta-feira, adiciona sábado e segunda
                if data_principal.weekday() == 4:  # 4 = sexta
                    sabado = data_principal + timedelta(days=1)
                    segunda = data_principal + timedelta(days=3)
                    datas.extend([sabado.strftime("%d-%m-%Y"), segunda.strftime("%d-%m-%Y")])
                
                print(f"   📅 DATAS EXPANDIDAS: {datas}")
                return datas
                
            except ValueError as e:
                print(f"   ⚠️ Data inválida '{data_param}', usando datas automáticas")
        
        # Comportamento padrão (quando não há data)
        hoje = datetime.now()
        datas = [
            hoje.strftime("%d-%m-%Y"),
            (hoje - timedelta(days=1)).strftime("%d-%m-%Y"),
            (hoje + timedelta(days=1)).strftime("%d-%m-%Y")
        ]
        
        print(f"   📅 DATAS AUTOMÁTICAS EXPANDIDAS: {datas}")
        return datas
    
    def _valor_no_nome_arquivo(self, arquivo: Path, valor: float) -> bool:
        """
        Verifica se o valor está no nome do arquivo
        """
        try:
            nome_sem_ext = arquivo.stem
            
            # Procura o valor formatado de diferentes formas
            valor_int = int(round(valor))
            patterns = [
                f"{valor:.2f}".replace('.', ','),  # 1234,56
                f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),  # 1.234,56
                str(valor_int),  # Parte inteira
                f"{valor:.0f}",  # Sem decimais
            ]
            
            for pattern in patterns:
                if pattern in nome_sem_ext:
                    return True
            
            return False
        except:
            return False
    
    def _valor_no_conteudo_arquivo(self, arquivo: Path, valor: float, tolerancia: float = 0.10) -> bool:
        try:
            print(f"      📖 LENDO CONTEÚDO COMPLETO DO ARQUIVO: {arquivo.name}")
            
            # Tenta ler TODAS as planilhas do arquivo
            try:
                planilhas = pd.read_excel(arquivo, sheet_name=None, engine='openpyxl')
                print(f"      📊 Total de planilhas: {len(planilhas)}")
            except Exception as e:
                print(f"      ❌ Erro ao ler todas as planilhas: {e}")
                # Se falhar, tenta ler apenas a primeira planilha
                try:
                    df = pd.read_excel(arquivo, engine='openpyxl')
                    planilhas = {'Sheet1': df}
                    print(f"      📊 Lida apenas a primeira planilha")
                except Exception as e2:
                    print(f"      ❌❌ Erro crítico ao ler arquivo: {e2}")
                    return False
            
            # BUSCA AGUESSIVA: Procura em TODAS as células de TODAS as planilhas
            for sheet_name, df in planilhas.items():
                if df.empty:
                    continue
                    
                print(f"      🔍 Buscando na planilha '{sheet_name}': {df.shape[0]} linhas x {df.shape[1]} colunas")
                
                # Converte TODO o DataFrame para string para busca mais abrangente
                df_str = df.astype(str)
                
                # Procura o valor em TODAS as células
                encontrou = False
                for col_idx, col_name in enumerate(df.columns):
                    for row_idx in range(len(df)):
                        valor_celula = df_str.iloc[row_idx, col_idx]
                        
                        # Pula células vazias
                        if valor_celula in ['nan', 'None', 'NaT', '']:
                            continue
                        
                        # Tenta extrair números da célula
                        try:
                            # Remove caracteres não numéricos (exceto ponto, vírgula e sinal)
                            valor_limpo = re.sub(r'[^\d,\-\.]', '', valor_celula)
                            
                            if not valor_limpo:
                                continue
                                
                            # Converte para float
                            valor_float = self._converter_valor_para_float(valor_limpo)
                            
                            if valor_float is not None:
                                # Verifica se é igual ao valor procurado (com tolerância)
                                if abs(valor_float - valor) <= tolerancia:
                                    print(f"      ✅✅✅ VALOR ENCONTRADO!")
                                    print(f"         Planilha: {sheet_name}")
                                    print(f"         Célula: {col_name}[{row_idx + 2}]")  # +2 porque Excel começa em 1 e tem header
                                    print(f"         Valor na célula: {valor_celula}")
                                    print(f"         Valor convertido: {valor_float}")
                                    print(f"         Valor procurado: {valor}")
                                    return True
                        except:
                            continue
                
                # Também procura o valor como string (formato brasileiro)
                for col_idx, col_name in enumerate(df.columns):
                    for row_idx in range(len(df)):
                        valor_celula = df_str.iloc[row_idx, col_idx]
                        
                        # Procura o valor formatado como string
                        valor_str_procurado = f"{valor:.2f}".replace('.', ',')  # 1234,56
                        if valor_str_procurado in valor_celula:
                            print(f"      ✅✅✅ VALOR ENCONTRADO COMO STRING!")
                            print(f"         Planilha: {sheet_name}")
                            print(f"         Célula: {col_name}[{row_idx + 2}]")
                            print(f"         Conteúdo: {valor_celula}")
                            print(f"         Padrão procurado: {valor_str_procurado}")
                            return True
            
            print(f"      ❌ Valor NÃO encontrado no arquivo")
            return False
            
        except Exception as e:
            print(f"      ❌❌ ERRO NA BUSCA NO CONTEÚDO: {e}")
            return False
    
    def _extrair_chassi_do_relatorio(self, arquivo: Path, valor: float) -> Optional[str]:
        try:
            df = pd.read_excel(arquivo)
            
            # Estratégia 1: Procurar coluna que contenha "chassi"
            for col in df.columns:
                if 'chassi' in str(col).lower():
                    # Retorna o primeiro chassi válido encontrado
                    for chassi in df[col].dropna():
                        chassi_str = str(chassi).strip()
                        if len(chassi_str) == 17:  # Chassi normalmente tem 17 caracteres
                            print(f"      ✅ Chassi encontrado na coluna '{col}': {chassi_str}")
                            return chassi_str
            
            # Estratégia 2: Se não encontrar coluna "chassi", usar lógica específica
            if len(df.columns) >= 8:
                # Supondo que o chassi está na coluna H (índice 7)
                coluna_chassi = df.columns[7]
                for chassi in df[coluna_chassi].dropna():
                    chassi_str = str(chassi).strip()
                    if len(chassi_str) == 17:
                        print(f"      ✅ Chassi encontrado na coluna fixa H: {chassi_str}")
                        return chassi_str
            
            # Estratégia 3: Procurar em qualquer coluna por valores que parecem chassis
            print(f"      🔍 Procurando chassi em todas as colunas...")
            for col in df.columns:
                for valor_celula in df[col].dropna():
                    valor_str = str(valor_celula).strip()
                    # Verifica se parece um chassi (17 caracteres alfanuméricos)
                    if len(valor_str) == 17 and valor_str.isalnum():
                        print(f"      ✅ Possível chassi encontrado na coluna '{col}': {valor_str}")
                        return valor_str
            
            print(f"      ❌ Nenhum chassi válido encontrado no arquivo")
            return None
            
        except Exception as e:
            print(f"❌ Erro ao extrair chassi: {e}")
            return None
    
    def _consultar_banco_dados(self, chassi: str, valor: float) -> Optional[ResultadoPan]:
        conn = None
        try:
            # Configuração da conexão Oracle
            user_oracle = os.getenv('USER_ORACLE')
            password = os.getenv('PASSWORD_ORACLE')
            dsn = os.getenv('DSN')

            if not all([user_oracle, password, dsn]):
                print("❌ Variáveis de ambiente Oracle não configuradas")
                return None

            # Estabelece conexão
            try:
                oracledb.init_oracle_client(lib_dir=r'C:\instantclient')
            except:
                pass  # Client já inicializado

            conn = oracledb.connect(
                user=user_oracle,
                password=password,
                dsn=dsn
            )

            cur = conn.cursor()

            # 1. Buscar cliente pelo chassi
            cur.execute(
                "SELECT CLIENTE FROM ofi_ficha_proprietario WHERE chassi = :chassi AND PROPRIETARIO_ATUAL = 'S'",
                {"chassi": chassi}
            )
            resultado_cliente = cur.fetchone()

            if not resultado_cliente:
                print(f"❌ Cliente não encontrado para chassi: {chassi}")
                
                # TENTATIVA ALTERNATIVA: Buscar por qualquer proprietário (não só o atual)
                cur.execute(
                    "SELECT CLIENTE FROM ofi_ficha_proprietario WHERE chassi = :chassi",
                    {"chassi": chassi}
                )
                resultado_cliente = cur.fetchone()
                
                if not resultado_cliente:
                    print(f"❌❌ Chassi não encontrado em nenhum proprietário: {chassi}")
                    return None
                
                print(f"⚠️  Cliente encontrado (proprietário não atual): {resultado_cliente[0]}")

            cliente = resultado_cliente[0]
            print(f"✅ Cliente encontrado: {cliente}")

            # 2. Buscar título/duplicata - ESTRATÉGIA MELHORADA
            resultados_titulos = []
            
            # PRIMEIRO: Busca exata com duplicata diferente de '00'
            cur.execute(
                """SELECT TITULO, DUPLICATA, VAL_TITULO 
                FROM fin_titulo 
                WHERE CLIENTE = :cliente 
                AND TIPO = 'CR'
                AND ROUND(VAL_TITULO, 2) = ROUND(:valor, 2)
                AND DUPLICATA != '00'
                ORDER BY DUPLICATA""",
                {"cliente": cliente, "valor": valor}
            )
            resultados_titulos.extend(cur.fetchall())

            # SEGUNDO: Se não encontrou, busca qualquer duplicata
            if not resultados_titulos:
                cur.execute(
                    """SELECT TITULO, DUPLICATA, VAL_TITULO 
                    FROM fin_titulo 
                    WHERE CLIENTE = :cliente 
                    AND ROUND(VAL_TITULO, 2) = ROUND(:valor, 2)
                    ORDER BY CASE WHEN DUPLICATA != '00' THEN 1 ELSE 2 END, DUPLICATA""",
                    {"cliente": cliente, "valor": valor}
                )
                resultados_titulos.extend(cur.fetchall())

            # TERCEIRO: Se ainda não encontrou, busca com tolerância de 1 real
            if not resultados_titulos:
                cur.execute(
                    """SELECT TITULO, DUPLICATA, VAL_TITULO 
                    FROM fin_titulo 
                    WHERE CLIENTE = :cliente 
                    AND ABS(VAL_TITULO - :valor) <= 1.00
                    ORDER BY ABS(VAL_TITULO - :valor), 
                                CASE WHEN DUPLICATA != '00' THEN 1 ELSE 2 END, 
                                DUPLICATA""",
                    {"cliente": cliente, "valor": valor}
                )
                resultados_titulos.extend(cur.fetchall())

            # QUARTA: Se ainda não encontrou, busca qualquer título do cliente (último recurso)
            if not resultados_titulos:
                cur.execute(
                    """SELECT TITULO, DUPLICATA, VAL_TITULO 
                    FROM fin_titulo 
                    WHERE CLIENTE = :cliente 
                    AND TIPO = 'CR'
                    ORDER BY DATA_EMISSAO DESC, 
                                CASE WHEN DUPLICATA != '00' THEN 1 ELSE 2 END
                    FETCH FIRST 1 ROWS ONLY""",
                    {"cliente": cliente}
                )
                resultados_titulos.extend(cur.fetchall())

            if resultados_titulos:
                # Pega o primeiro resultado (mais relevante)
                titulo, duplicata, val_titulo = resultados_titulos[0]
                
                # Log detalhado
                if len(resultados_titulos) > 1:
                    print(f"📊 Múltiplos títulos encontrados ({len(resultados_titulos)}), usando o mais relevante")
                
                print(f"✅✅✅ DADOS ENCONTRADOS NO BANCO: Título {titulo}, Duplicata {duplicata}")
                return ResultadoPan(
                    titulo=str(titulo),
                    duplicata=str(duplicata),
                    valor=float(val_titulo)
                )

            print(f"❌ Nenhum título encontrado no banco para cliente {cliente}, valor {valor}")
            return None

        except Exception as e:
            print(f"❌ Erro na consulta ao banco: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def _debug_conteudo_arquivo(self, arquivo: Path, max_linhas: int = 5):
        try:
            print(f"\n      🧪 DEBUG DO ARQUIVO: {arquivo.name}")
            planilhas = pd.read_excel(arquivo, sheet_name=None, engine='openpyxl')
            
            for sheet_name, df in planilhas.items():
                if df.empty:
                    print(f"         Planilha '{sheet_name}': VAZIA")
                    continue
                    
                print(f"         Planilha '{sheet_name}': {df.shape[0]} linhas x {df.shape[1]} colunas")
                print(f"         Colunas: {list(df.columns)}")
                
                # Mostra algumas linhas de dados
                for i in range(min(max_linhas, len(df))):
                    linha_str = " | ".join([str(df.iloc[i, j]) for j in range(min(5, len(df.columns)))])
                    print(f"         Linha {i+1}: {linha_str}")
                    
        except Exception as e:
            print(f"         ❌ Erro no debug: {e}")

    def processar_extrato_com_data(self, caminho_arquivo: str, data_busca: str) -> List[ResultadoPan]:
        try:
            print(f"\n" + "="*60)
            print(f"🔍 INICIANDO PROCESSAMENTO DO EXTRATO PAN")
            print(f"📅 DATA ESPECÍFICA: {data_busca}")
            print("="*60)
            
            # 1. Upload e leitura do arquivo
            df_extrato = self._ler_extrato_itaú(caminho_arquivo)
            
            # 2. Filtragem de lançamentos relevantes
            valores_pan = self._filtrar_lancamentos_pan(df_extrato)
            
            if not valores_pan:
                print("❌ Nenhum lançamento PAN encontrado no extrato")
                return []
            
            print(f"✅ Valores PAN encontrados: {valores_pan}")
            
            # 3. Busca em diretório de rede COM DATA ESPECÍFICA
            resultados = []
            
            for valor in valores_pan:
                print(f"\n💰 PROCESSANDO VALOR: R$ {valor:,.2f}")
                
                # Buscar o arquivo correspondente ao valor NA DATA ESPECÍFICA
                arquivo_encontrado = self._buscar_arquivo_por_valor_com_data(valor, data_busca)
                
                if arquivo_encontrado:
                    # 4. Extração de informações do relatório
                    chassi = self._extrair_chassi_do_relatorio(arquivo_encontrado, valor)
                    
                    if chassi:
                        print(f"✅ Chassi encontrado: {chassi}")
                        # Consulta no banco de dados
                        resultado_banco = self._consultar_banco_dados(chassi, valor)
                        
                        if resultado_banco:
                            resultados.append(resultado_banco)
                            print(f"✅✅✅ VALOR PROCESSADO COM SUCESSO: R$ {valor:,.2f}")
                            print(f"   📝 Dados: Título {resultado_banco.titulo}, Duplicata {resultado_banco.duplicata}")
                        else:
                            print(f"⚠️  Dados não encontrados no banco para chassi {chassi}")
                    else:
                        print(f"⚠️  Chassi não encontrado no relatório")
                else:
                    print(f"❌ Arquivo não encontrado para o valor R$ {valor:,.2f} na data {data_busca}")

            # DEBUG FINAL
            print(f"\n" + "="*60)
            print("🔍 DEBUG FINAL - TODOS OS RESULTADOS COLETADOS")
            print("="*60)
            print(f"📊 Total de valores PAN no extrato: {len(valores_pan)}")
            print(f"📊 Total de resultados processados: {len(resultados)}")
            
            for i, resultado in enumerate(resultados):
                print(f"   {i+1}. Título: {resultado.titulo}, Duplicata: {resultado.duplicata}, Valor: R$ {resultado.valor:,.2f}")
            
            print(f"📊 RESULTADO FINAL: {len(resultados)} registros processados")
            return resultados
            
        except Exception as e:
            print(f"❌ ERRO NO PROCESSAMENTO: {e}")
            raise
    
    def _buscar_arquivo_por_valor_com_data(self, valor: float, data_busca: str) -> Optional[Path]:
        print(f"   🔍 Buscando arquivo para R$ {valor:,.2f}")
        print(f"   📅 DATA ESPECÍFICA: {data_busca}")
        
        pasta_data = Path(self.base_dir_rede) / data_busca
        
        if not pasta_data.exists():
            print(f"   ❌ Pasta não existe: {data_busca}")
            return None
        
        print(f"   📂 Verificando pasta: {data_busca}")
        
        # Busca arquivos Excel na pasta
        arquivos = list(pasta_data.glob("*.xlsx")) + list(pasta_data.glob("*.xls"))
        arquivos = [arq for arq in arquivos if not arq.name.startswith('~$')]
        
        print(f"   📄 Arquivos encontrados: {len(arquivos)}")
        
        for arquivo in arquivos:
            print(f"      🔎 Analisando: {arquivo.name}")
            
            # Verifica se o valor está no nome do arquivo
            if self._valor_no_nome_arquivo(arquivo, valor):
                print(f"      ✅ ENCONTRADO no nome do arquivo!")
                return arquivo
            
            # Ou verifica se o valor está no conteúdo do arquivo
            if self._valor_no_conteudo_arquivo(arquivo, valor):
                print(f"      ✅ ENCONTRADO no conteúdo do arquivo!")
                return arquivo
            
            print(f"      ❌ Valor não encontrado em {arquivo.name}")
        
        print(f"   ❌❌❌ NENHUM ARQUIVO ENCONTRADO PARA R$ {valor:,.2f} na data {data_busca}")
        return None