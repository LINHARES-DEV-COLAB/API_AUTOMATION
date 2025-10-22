import pandas as pd
from datetime import datetime
import tempfile 
import os
from pathlib import Path
import traceback
from typing import Dict, List, Optional

class BaixasPanService:
    def __init__(self):
        self.BASE_DIR_REDE = r"\\172.17.67.14\Ares Motos\controladoria\financeiro\06.CONTAS A RECEBER\11.RELATÓRIOS BANCO PAN"
    
    def processar_extrato(self, arquivo_path: str) -> Dict:

        try:
            from APP.Core.pan import extrair_valores_pan_do_arquivo, pipeline_pan_multidata
            from main import debug_pastas_pan

            valores_extraidos = extrair_valores_pan_do_arquivo(arquivo_path, termo_lanc="pan")

            if not valores_extraidos:
                return{
                    "sucesso":False,
                    "erro":"Nenhum valor PAN encontrado no extrato",
                    "valores_extraidos": []
                }
            pastas_disponiveis = debug_pastas_pan(self.BASE_DIR_REDE, dias_para_verificar=2)
            pastas_para_buscar = pastas_disponiveis[:4]

            if not datas_para_buscar:
                return {
                    "sucesso": False,
                    "erro": "Nenhuma pasta PAN encontrada",
                    "pastas_buscadas": pastas_disponiveis
                }
            
            pastas_disponiveis = debug_pastas_pan(self.BASE_DIR_REDE, dias_para_verificar=5)
            datas_para_buscar = pastas_disponiveis[:4]
            
            if not datas_para_buscar:
                return {
                    "sucesso": False,
                    "erro": "Nenhuma pasta PAN encontrada",
                    "pastas_buscadas": pastas_disponiveis
                }
                
            df_resultado = pipeline_pan_multidata(
                arquivo_path,
                self.BASE_DIR_REDE,
                datas_para_buscar,
                atol=0.10,
                usar_valor_absoluto=True,
                recursivo=True
            )

            resultado = self._preparar_resposta(df_resultado, valores_extraidos, datas_para_buscar)
            resultado["sucesso"] = True
            
            return resultado
            
        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro no processamento: {str(e)}",
                "traceback": traceback.format_exc()
            }
    def buscar_valores_diretos(self, valores: List[float], datas: Optional[List[str]] = None) -> Dict:
        """
        Busca direta por valores específicos
        """
        try:
            from Core.pan import buscar_por_parte_inteira
            from main import debug_pastas_pan
            
            # Se não especificou datas, usar as disponíveis
            if not datas:
                pastas_disponiveis = debug_pastas_pan(self.BASE_DIR_REDE, dias_para_verificar=5)
                datas = pastas_disponiveis[:4]
            
            resultados_combinados = pd.DataFrame()
            
            for data_str in datas:
                pasta_data = Path(self.BASE_DIR_REDE) / data_str
                if pasta_data.exists():
                    df_busca = buscar_por_parte_inteira(pasta_data, valores, atol=0.10)
                    if not df_busca.empty:
                        df_busca["__DATA_ORIGEM__"] = data_str
                        resultados_combinados = pd.concat([resultados_combinados, df_busca], ignore_index=True)
            
            # Converter para formato de resposta
            resultados_json = self._dataframe_para_json(resultados_combinados)
            
            return {
                "sucesso": True,
                "valores_buscados": valores,
                "datas_buscadas": datas,
                "resultados": resultados_json,
                "total_encontrados": len(resultados_combinados)
            }
            
        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro na busca direta: {str(e)}"
            }
    def listar_pastas_disponiveis(self) -> Dict:

        try:
            from main import debug_pastas_pan
            
            pastas = debug_pastas_pan(self.BASE_DIR_REDE, dias_para_verificar=7)
            
            return {
                "sucesso": True,
                "pastas_disponiveis": pastas,
                "total_pastas": len(pastas),
                "caminho_rede": self.BASE_DIR_REDE
            }
            
        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao listar pastas: {str(e)}"
            }
    
    def _preparar_resposta(self, df_resultado: pd.DataFrame, valores_extraidos: List[float], datas_buscadas: List[str]) -> Dict:
        """Prepara resposta formatada"""
        
        # Estatísticas
        total_encontrados = len(df_resultado) if not df_resultado.empty else 0
        
        # Valores encontrados vs não encontrados
        valores_encontrados = set()
        if not df_resultado.empty and '__VALOR_TITULO__' in df_resultado.columns:
            valores_encontrados = set(df_resultado["__VALOR_TITULO__"].dropna().astype(float))
        
        valores_nao_encontrados = [
            valor for valor in valores_extraidos 
            if not any(abs(valor - v) <= 0.10 for v in valores_encontrados)
        ]
        
        # Resultados detalhados
        resultados_detalhados = self._dataframe_para_json(df_resultado) if not df_resultado.empty else []
        
        return {
            "estatisticas": {
                "valores_extraidos": len(valores_extraidos),
                "valores_encontrados": len(valores_encontrados),
                "valores_nao_encontrados": len(valores_nao_encontrados),
                "total_registros": total_encontrados,
                "datas_buscadas": datas_buscadas,
                "datas_com_resultados": list(set(df_resultado["__DATA_ORIGEM__"])) if not df_resultado.empty else []
            },
            "valores_extraidos": valores_extraidos,
            "valores_nao_encontrados": valores_nao_encontrados,
            "resultados": resultados_detalhados,
            "timestamp": datetime.now().isoformat()
        }
    
    def _dataframe_para_json(self, df: pd.DataFrame) -> List[Dict]:
        """Converte DataFrame para JSON"""
        if df.empty:
            return []
        
        # Selecionar colunas relevantes
        colunas_relevantes = [
            '__Arquivo__', '__Planilha__', '__Coluna_Encontrado__', 
            '__VALOR_NUM__', '__VALOR_ORIGINAL__', '__TITULO__', 
            '__DUPLICATA__', '__VALOR_TITULO__', '__DATA_ORIGEM__'
        ]
        
        colunas_disponiveis = [col for col in colunas_relevantes if col in df.columns]
        df_filtrado = df[colunas_disponiveis]
        
        return df_filtrado.fillna('').to_dict('records')