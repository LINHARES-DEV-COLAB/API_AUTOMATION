# APP/Services/base_simple_automation.py
from APP.Interfaces.automation_interface import AutomationCommand
import logging
from typing import Any, Dict

class BaseSimpleAutomation(AutomationCommand):
    """Classe base para automações simples que usam principalmente strings"""
    
    def __init__(self, automation_name: str, required_params: list = None):
        self.automation_name = automation_name
        self.required_params = required_params or []
        self.logger = logging.getLogger(__name__)
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validação padrão para parâmetros obrigatórios"""
        self.logger.info(f"🔍 Validando parâmetros para {self.automation_name}")
        
        for param in self.required_params:
            if param not in parameters:
                self.logger.error(f"❌ Parâmetro obrigatório faltando: {param}")
                return False
        
        self.logger.info(f"✅ Parâmetros válidos para {self.automation_name}")
        return True
    
    def get_required_parameters(self) -> list:
        """Retorna parâmetros obrigatórios"""
        return self.required_params
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Método abstrato que deve ser implementado pelas subclasses"""
        raise NotImplementedError("Método execute deve ser implementado pela subclasse")