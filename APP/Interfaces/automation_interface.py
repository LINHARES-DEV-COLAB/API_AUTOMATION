# APP/Interfaces/automation_interface.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class AutomationCommand(ABC):
    """Interface base para todos os comandos de automação"""
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Valida se os parâmetros necessários estão presentes"""
        pass
    
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Executa a automação com os parâmetros fornecidos"""
        pass
    def get_required_parameters(self) -> Optional[list]:
        """Retorna uma descrição dos parâmetros necessários (opcional)"""
        return None