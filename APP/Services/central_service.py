

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



# APP/Services/central_service.py

# APP/Services/central_service.py

# APP/Services/automation_factory.py
# APP/Services/automation_factory.py
import logging
import os

logger = logging.getLogger(__name__)

class AutomationFactory:
    def __init__(self):
        self.automation_mapping = {
            'fidc': 'APP.Services.fidc_service.FIDCAutomation',
            'baixas_pan': 'APP.Services.pan_service.PanService',
            'ihs': 'APP.Services.ihs_service.IHSService',  # ← NOVO
            'cnh': 'APP.Services.cnh_service.CNHService',  # ← NOVO
            'cdc': 'APP.Services.cdc_service.CDCService',  # ← NOVO
            'preparacao_baixas': 'APP.Services.preparacao_service.PreparacaoBaixasService',  # ← NOVO
            'solicitacao_baixas': 'APP.Services.solicitacao_service.SolicitacaoBaixasService'  # ← NOVO
        }
    
    def create_command(self, automation_id: str, script_path: str = None):
        """Cria o comando baseado no script_path"""
        try:
            logger.info(f"🔍 Factory criando: ID={automation_id}, Script={script_path}")
            
            # Determina o tipo baseado no script_path ou ID
            automation_type = self._infer_type_from_script(script_path, automation_id)
            logger.info(f"🎯 Tipo inferido: {automation_type}")
            
            if not automation_type:
                logger.error("❌ Não foi possível determinar o tipo da automação")
                return None
            
            # Importa e instancia a classe correta
            module_class = self.automation_mapping.get(automation_type)
            if not module_class:
                logger.error(f"❌ Tipo de automação não mapeado: {automation_type}")
                return None
            
            module_name, class_name = module_class.rsplit('.', 1)
            module = __import__(module_name, fromlist=[class_name])
            automation_class = getattr(module, class_name)
            
            logger.info(f"✅ Instanciando: {automation_class.__name__}")
            return automation_class()
            
        except Exception as e:
            logger.error(f"❌ Erro no factory: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None
    
    def _infer_type_from_script(self, script_path: str, automation_id: str) -> str:
        """Infere o tipo da automação baseado no script_path ou ID"""
        # Primeiro tenta pelo script_path
        if script_path:
            script_lower = script_path.lower()
            if 'fidc' in script_lower:
                return 'fidc'
            elif 'pan' in script_lower:
                return 'baixas_pan'
            elif 'ihs' in script_lower or 'driver' in script_lower:  # ← NOVO
                return 'ihs'
            elif 'cnh' in script_lower:  # ← NOVO
                return 'cnh'
            elif 'cdc' in script_lower or 'conciliacao' in script_lower:  # ← NOVO
                return 'cdc'
            elif 'preparacao' in script_lower or 'baixas' in script_lower:  # ← NOVO
                return 'preparacao_baixas'
            elif 'solicitacao' in script_lower:  # ← NOVO
                return 'solicitacao_baixas'
        
        # Fallback: usa o ID
        id_lower = automation_id.lower()
        if 'fidc' in id_lower:
            return 'fidc'
        elif 'pan' in id_lower:
            return 'baixas_pan'
        elif 'ihs' in id_lower or 'driver' in id_lower:  # ← NOVO
            return 'ihs'
        elif 'cnh' in id_lower:  # ← NOVO
            return 'cnh'
        elif 'cdc' in id_lower or 'conciliacao' in id_lower:  # ← NOVO
            return 'cdc'
        elif 'preparacao' in id_lower:  # ← NOVO
            return 'preparacao_baixas'
        elif 'solicitacao' in id_lower:  # ← NOVO
            return 'solicitacao_baixas'
        
        
        return None