from datetime import datetime
from typing import List, Optional, Dict, Any

# Schemas simples para Flask (sem Pydantic)
class ProcessamentoRequest:
    def __init__(self, arquivo_path: str, banco: str = "PAN", 
                 datas_para_buscar: List[str] = None, tolerancia: float = 0.10):
        self.arquivo_path = arquivo_path
        self.banco = banco
        self.datas_para_buscar = datas_para_buscar or []
        self.tolerancia = tolerancia

class ProcessamentoResponse:
    def __init__(self, job_id: str, status: str, mensagem: str, 
                 total_encontrados: int = 0, total_nao_encontrados: int = 0,
                 arquivo_resultado: str = None, arquivo_nao_encontrados: str = None):
        self.job_id = job_id
        self.status = status
        self.mensagem = mensagem
        self.total_encontrados = total_encontrados
        self.total_nao_encontrados = total_nao_encontrados
        self.arquivo_resultado = arquivo_resultado
        self.arquivo_nao_encontrados = arquivo_nao_encontrados
    
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'status': self.status,
            'mensagem': self.mensagem,
            'total_encontrados': self.total_encontrados,
            'total_nao_encontrados': self.total_nao_encontrados,
            'arquivo_resultado': self.arquivo_resultado,
            'arquivo_nao_encontrados': self.arquivo_nao_encontrados
        }

class StatusProcessamento:
    def __init__(self, job_id: str, status: str, progresso: int, mensagem: str, resultados=None):
        self.job_id = job_id
        self.status = status
        self.progresso = progresso
        self.mensagem = mensagem
        self.resultados = resultados or []
    
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'status': self.status,
            'progresso': self.progresso,
            'mensagem': self.mensagem,
            'resultados': self.resultados
        }