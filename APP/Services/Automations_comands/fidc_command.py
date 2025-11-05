# APP/Services/Automations_comands/fidc_command.py

from APP.Interfaces.automation_interface import automation_command
import logging

class fidc_command(automation_command):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_parameters(self, params: dict) -> bool:
        self.logger.info("🔍 Validando parâmetros FIDC")
        
        # Apenas arquivo Excel é obrigatório
        if 'arquivo_excel' not in params or not params['arquivo_excel']:
            self.logger.error("❌ Parâmetro 'arquivo_excel' é obrigatório")
            return False
        
        # Lojas é opcional
        if 'lojas' not in params:
            params['lojas'] = []
        
        self.logger.info("✅ Parâmetros validados com sucesso")
        return True
    
    def execute(self, params):
        self.logger.info("🚀 Executando comando FIDC")
        
        try:
            from APP.Services.fidc_service import FIDCAutomation
            
            automation = FIDCAutomation()
            resultado = automation.execute(params)
            
            self.logger.info("✅ Comando FIDC executado com sucesso")
            
            return {
                "status": "success",  # ← Status interno do comando
                "data": resultado,
                "automation": "fidc"
            }
        
        except Exception as e:
            self.logger.error(f"❌ Erro no comando FIDC: {e}")
            return {
                "status": "error",  # ← Status interno do comando  
                "message": str(e),
                "automation": "fidc"
            }