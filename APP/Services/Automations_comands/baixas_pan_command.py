from APP.Interfaces.automation_interface import automation_command
from ..pan_service import PanService     
from datetime import datetime, timedelta


class baixas_pan_command(automation_command):
    def validate_parameters(self, params: dict) -> bool:
        # Valida se tem o arquivo (os outros parâmetros são opcionais ou calculados)
        return "arquivo_excel" in params
    
    def execute(self, params):
        #chama o serviço
        try:
            file = params["file"]
            data_processamento = self._calcular_data_regra()
            

            resultado = PanService.processar_extrato(file ,data_processamento )
            return {
                "status": "success",
                "data": resultado,
                "automation": "baixas_pan",
                "parametros_utilizados": {
                    "arquivo_excel": file,
                    "data_processamento": data_processamento,
                }
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "automation": "baixas_pan"
            }
        
    def _calcular_data_regra(self) -> str:
        hoje = datetime.now()    

        if hoje.weekday() == 0: 
            data_calculada = hoje - timedelta(days=2)
        else:
            data_calculada = hoje

        return data_calculada.strftime("%d-%m-%Y")
