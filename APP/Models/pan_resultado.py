from dataclasses import dataclass
from typing import Optional

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