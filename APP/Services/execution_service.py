# APP/Services/execution_service.py

from datetime import datetime
import uuid
from APP.Config.supa_config import db
from APP.Models.executions_model import Execution

class ExecutionService:
    @staticmethod
    def create_execution(automation_id: str, triggered_by: str = None):
        """Cria um novo registro de execução"""
        execution_id = str(uuid.uuid4())
        
        execution = Execution(
            id=execution_id,
            automation_id=automation_id,
            triggered_by=triggered_by or 'system',
            status='running',
            start_time=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        try:
            db.session.add(execution)
            db.session.commit()
            print(f"✅ Execução criada: {execution_id}")
            return execution_id
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar execução: {e}")
            return f"temp-{uuid.uuid4()}"

    @staticmethod
    def update_execution_status(execution_id: str, status: str, output_log: str = None, error_log: str = None):
        """Atualiza o status de uma execução - VERSÃO CORRIGIDA"""
        try:
            execution = Execution.query.get(execution_id)
            if execution:
                execution.status = status
                execution.end_time = datetime.utcnow()
                
                if output_log:
                    execution.output_log = output_log[:5000] if output_log else None
                if error_log:
                    execution.error_log = error_log[:5000] if error_log else None
                
                # ⭐ REMOVI O exit_code daqui pois não está no seu model
                db.session.commit()
                print(f"✅ Execução {execution_id} atualizada para status: {status}")
            else:
                print(f"⚠️ Execução {execution_id} não encontrada")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao atualizar execução {execution_id}: {e}")

    @staticmethod
    def complete_execution(execution_id: str, output_data: dict):
        """Marca execução como concluída com sucesso - VERSÃO CORRIGIDA"""
        output_log = str(output_data)[:5000] if output_data else "Execução concluída"
        
        ExecutionService.update_execution_status(
            execution_id=execution_id,
            status='completed',
            output_log=output_log
        )

    @staticmethod
    def fail_execution(execution_id: str, error_message: str):
        """Marca execução como falha - VERSÃO CORRIGIDA"""
        ExecutionService.update_execution_status(
            execution_id=execution_id,
            status='failed',
            error_log=error_message[:5000] if error_message else "Erro desconhecido"
        )