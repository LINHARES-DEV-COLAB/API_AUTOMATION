# pan_processor.py - VERSÃO INDEPENDENTE
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any, Iterable
import logging
from datetime import datetime
import os
import re
import unicodedata

from ..Config.settings import config

logger = logging.getLogger(__name__)

class PanProcessor:
    def __init__(self):
        self.pan_network_path = config.PAN_NETWORK_PATH
        
        # Constantes
        self._MINUS_CHARS = ["-", "−", "–", "—"] 
        self._NBSP = "\u00A0"
        self._NNBS = "\u202F"
    
    def processar_pan_multidata(self, caminho_arquivo: str, base_dir_rede: str, 
                              datas_para_buscar: List[str], atol: float = 0.10) -> List[Dict[str, Any]]:
        """
        Processamento PAN completo - versão independente
        """
        logger.info(f"Processando arquivo: {caminho_arquivo}")
        logger.info(f"Buscando nas datas: {datas_para_buscar}")
        
        try:
            # 1. Extrair valores do arquivo Excel
            valores_alvo = self._extrair_valores_excel(caminho_arquivo)
            if not valores_alvo:
                logger.warning("Nenhum valor numérico encontrado no arquivo de entrada.")
                return []
            
            logger.info(f"🎯 VALORES EXTRAÍDOS: {sorted(valores_alvo)}")
            logger.info(f"📅 BUSCANDO NAS DATAS: {datas_para_buscar}")
            
            todos_resultados = []
            
            # 2. Buscar em cada data
            for data_str in datas_para_buscar:
                pasta_data = Path(base_dir_rede) / data_str
                logger.info(f"🔍 Verificando pasta: {pasta_data}")
                
                if pasta_data.exists():
                    logger.info(f"   ✅ Pasta encontrada: {data_str}")
                    
                    # Buscar valores nas planilhas da pasta
                    resultados_data = self._buscar_nas_planilhas(pasta_data, valores_alvo)
                    
                    if resultados_data:
                        # Adicionar data de origem a cada resultado
                        for resultado in resultados_data:
                            resultado["data_origem"] = data_str
                        
                        todos_resultados.extend(resultados_data)
                        logger.info(f"   📊 Encontrados {len(resultados_data)} registros na data {data_str}")
                    else:
                        logger.info(f"   ❌ Nenhum resultado na data {data_str}")
                else:
                    logger.info(f"   ⚠️ Pasta não existe: {data_str}")
            
            logger.info(f"📈 PROCESSAMENTO CONCLUÍDO: {len(todos_resultados)} registros encontrados")
            return todos_resultados
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento PAN: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extrair_valores_excel(self, caminho_arquivo: str) -> List[float]:
        """
        Extrai valores numéricos de um arquivo Excel
        """
        try:
            df = pd.read_excel(caminho_arquivo)
            logger.info(f"📊 Arquivo lido: {len(df)} linhas, colunas: {df.columns.tolist()}")
            
            # Procurar todas as colunas numéricas
            valores = []
            for coluna in df.columns:
                try:
                    # Tentar converter coluna para numérica
                    col_numeric = pd.to_numeric(df[coluna], errors='coerce')
                    valores_coluna = col_numeric.dropna().unique().tolist()
                    valores.extend([float(v) for v in valores_coluna if abs(v) > 0.01])  # Filtrar valores muito pequenos
                except:
                    continue
            
            # Remover duplicados e retornar
            valores_unicos = list(set([round(v, 2) for v in valores]))
            logger.info(f"💰 Valores extraídos: {len(valores_unicos)} valores únicos")
            
            return valores_unicos
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair valores do Excel: {e}")
            return []
    
    def _buscar_nas_planilhas(self, pasta: Path, valores_alvo: List[float]) -> List[Dict[str, Any]]:
        """
        Busca valores nas planilhas de uma pasta
        """
        resultados = []
        
        # Encontrar todos os arquivos Excel
        arquivos = list(pasta.glob("**/*.xlsx")) + list(pasta.glob("**/*.xls"))
        arquivos = [arq for arq in arquivos if not arq.name.startswith('~$')]
        
        logger.info(f"🔍 Procurando em {len(arquivos)} arquivos...")
        
        for arquivo in arquivos:
            try:
                logger.info(f"📖 Processando: {arquivo.name}")
                
                # Ler todas as planilhas do arquivo
                planilhas = pd.read_excel(arquivo, sheet_name=None, engine='openpyxl')
                
                for nome_planilha, df in planilhas.items():
                    if df.empty:
                        continue
                    
                    # Buscar valores em todas as colunas numéricas
                    encontros_planilha = self._buscar_valores_na_dataframe(df, valores_alvo, arquivo.name, nome_planilha)
                    resultados.extend(encontros_planilha)
                    
            except Exception as e:
                logger.error(f"   💥 Erro no arquivo {arquivo.name}: {e}")
                continue
        
        return resultados
    
    def _buscar_valores_na_dataframe(self, df: pd.DataFrame, valores_alvo: List[float], 
                                   nome_arquivo: str, nome_planilha: str) -> List[Dict[str, Any]]:
        """
        Busca valores alvo em um DataFrame
        """
        encontros = []
        
        # Procurar em todas as colunas
        for col_idx, coluna in enumerate(df.columns):
            for linha_idx, valor in enumerate(df[coluna]):
                if pd.isna(valor):
                    continue
                
                # Tentar converter para número
                try:
                    valor_numerico = float(valor)
                    
                    # Verificar se corresponde a algum valor alvo (com tolerância)
                    for valor_alvo in valores_alvo:
                        if abs(valor_numerico - valor_alvo) <= 0.10:  # Tolerância de R$ 0,10
                            # Encontrou correspondência!
                            resultado = {
                                "arquivo": nome_arquivo,
                                "planilha": nome_planilha,
                                "coluna": coluna,
                                "linha": linha_idx + 2,  # +2 para linha do Excel (header + 1-based)
                                "valor_encontrado": valor_numerico,
                                "valor_alvo": valor_alvo,
                                "diferenca": abs(valor_numerico - valor_alvo),
                                "celula": f"{coluna}{linha_idx + 2}",
                                "dados_linha": self._extrair_dados_linha(df, linha_idx)
                            }
                            encontros.append(resultado)
                            logger.info(f"   🎯 ENCONTRADO: R$ {valor_alvo} → R$ {valor_numerico} em {coluna}{linha_idx + 2}")
                            
                except (ValueError, TypeError):
                    # Não é número, continuar procurando
                    continue
        
        return encontros
    
    def _extrair_dados_linha(self, df: pd.DataFrame, linha_idx: int) -> Dict[str, Any]:
        """
        Extrai dados relevantes da linha onde o valor foi encontrado
        """
        try:
            linha = df.iloc[linha_idx]
            dados = {}
            
            # Extrair até 5 colunas mais relevantes
            for i, (coluna, valor) in enumerate(linha.items()):
                if i >= 5:  # Limitar a 5 colunas
                    break
                if pd.notna(valor):
                    dados[str(coluna)] = str(valor)
            
            return dados
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados da linha: {e}")
            return {"erro": str(e)}
    
    def _converter_para_float_brasileiro(self, valor) -> Optional[float]:
        """
        Converte valores em formato brasileiro para float
        """
        if pd.isna(valor):
            return None
            
        if isinstance(valor, (int, float)):
            return float(valor)
        
        try:
            valor_str = str(valor).strip()
            # Remover R$, espaços, etc
            valor_str = re.sub(r'[^\d,\.]', '', valor_str)
            
            # Formato brasileiro: 1.234,56 ou 1234,56
            if ',' in valor_str:
                if '.' in valor_str:
                    # Formato 1.234,56 - remove pontos, substitui vírgula
                    valor_str = valor_str.replace('.', '').replace(',', '.')
                else:
                    # Formato 1234,56 - substitui vírgula
                    valor_str = valor_str.replace(',', '.')
            
            return float(valor_str)
        except:
            return None

    # Método mantido para compatibilidade
    def extrair_valores_pan(self, caminho_arquivo: str) -> List[float]:
        """Alias para _extrair_valores_excel"""
        return self._extrair_valores_excel(caminho_arquivo)