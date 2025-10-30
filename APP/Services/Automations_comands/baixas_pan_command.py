from APP.Interfaces.automation_interface import automation_command
from ..pan_service import PanService     


class baixas_pan_command(automation_command):
    def validate_parameters(self, params: dict) -> bool:
        # exemplo de rota que não precisa de parâmetros
        return True 
    
    def execute(self, params):
        #chama o serviço
        try:
            resultado = PanService.processar_extrato()
            return {
                "status": "success",
                "data": resultado,
                "automation": "fidc"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "automation": "fidc"
            }

