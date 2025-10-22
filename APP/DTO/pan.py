from typing import Optional

class FinTituloDTO:
    def __init__(self, titulo: Optional[float] = None, duplicata: Optional[str] = None, val_titulo: Optional[str] = None):
        self.titulo = titulo
        self.duplicata = duplicata
        self.val_titulo = val_titulo

class ProcessamentoJob:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = "pendente"
        self.progresso = 0
        self.mensagem = ""
        self.resultados = []
        self.arquivo_resultado = None
        self.arquivo_nao_encontrados = None