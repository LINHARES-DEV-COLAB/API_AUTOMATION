from APP.Services.Automations_comands import fidc_command, baixas_pan_command, abrir_driver_ihs_command, baixa_arquivos_cnh_command, conciliacao_cdc_honda_command, preparacao_baixas_command, solicitacao_baixas_command


# class AutomationFactory:
#     def create_command(self, automation_id: str):
#         # 3.1 - Mapeia ID para Command específico
#         commands = {
#             "abrir_driver_ihs": abrir_driver_ihs_command(),
#             "fidc": fidc_command(),
#             "baixa_arquivos_cnh": baixa_arquivos_cnh_command(),
#             "conciliacao_cdc_honda": conciliacao_cdc_honda_command(),
#             "baixas_pan": baixas_pan_command(),
#             "preparacao_baixas": preparacao_baixas_command(),
#             "solicitacao_baixas": solicitacao_baixas_command(),
#         }
        
#         # 3.2 - Retorna comando ou None se não existir
#         return commands.get(automation_id)
    
# CORRETO - importe a CLASSE de dentro do módulo
from APP.Services.Automations_comands.fidc_command import fidc_command

class AutomationFactory:
    def create_command(self, automation_id: str):
        print(f"🔍 DEBUG FACTORY - automation_id recebido: {automation_id}")
        
        # DEBUG final
        print(f"🔍 DEBUG FACTORY - fidc_command classe: {fidc_command}")
        print(f"🔍 DEBUG FACTORY - tipo da classe: {type(fidc_command)}")
        
        commands = {
            "fidc": fidc_command(),  # ← Agora é a CLASSE instanciada
        }
        
        command = commands.get(automation_id)
        print(f"🔍 DEBUG FACTORY - command instanciado: {command}")
        
        return command
        
        # ... resto do código
    