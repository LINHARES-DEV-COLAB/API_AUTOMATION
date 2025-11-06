# APP/Services/execution_service.py

from datetime import datetime
import uuid
from APP.Config.supa_config import db
from APP.Models.executions_model import Execution
from APP.Models.execution_status_log_model import ExecutionStatusLog

class ExecutionService:
    
    @staticmethod
    def _create_status_log(execution_id: str, status_before: str, status_after: str, 
                          changed_by: str = None, note: str = None):
        """Cria registro no histórico de status"""
        try:
            log_id = str(uuid.uuid4())
            
            status_log = ExecutionStatusLog(
                id=log_id,
                execution_id=execution_id,
                status_before=status_before,
                status_after=status_after,
                changed_by=changed_by or 'system',
                note=note,
                changed_at=datetime.utcnow()
            )
            
            db.session.add(status_log)
            # Não faz commit aqui - deixa para o método principal
            print(f"📝 Log de status criado: {status_before} -> {status_after}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar log de status: {e}")
            return False

    @staticmethod
    def create_execution(automation_id: str, triggered_by: str = None, note: str = None):
        """Cria um novo registro de execução com histórico"""
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
            
            # Cria o log do status inicial
            ExecutionService._create_status_log(
                execution_id=execution_id,
                status_before=None,  # Primeiro status
                status_after='running',
                changed_by=triggered_by or 'system',
                note=note or "Execução iniciada"
            )
            
            db.session.commit()
            print(f"✅ Execução criada: {execution_id}")
            return execution_id
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar execução: {e}")
            return f"temp-{uuid.uuid4()}"

    @staticmethod
    def update_execution_status(execution_id: str, status: str, output_log: str = None, 
                              error_log: str = None, changed_by: str = None, note: str = None):
        """Atualiza o status de uma execução com histórico"""
        try:
            execution = Execution.query.get(execution_id)
            if execution:
                status_before = execution.status  # Salva o status anterior
                
                execution.status = status
                execution.end_time = datetime.utcnow() if status in ['completed', 'failed'] else execution.end_time
                
                if output_log:
                    execution.output_log = output_log[:5000] if output_log else None
                if error_log:
                    execution.error_log = error_log[:5000] if error_log else None
                
                # Cria log do status
                ExecutionService._create_status_log(
                    execution_id=execution_id,
                    status_before=status_before,
                    status_after=status,
                    changed_by=changed_by or 'system',
                    note=note or f"Status alterado: {status_before} -> {status}"
                )
                
                db.session.commit()
                print(f"✅ Execução {execution_id} atualizada para status: {status}")
            else:
                print(f"⚠️ Execução {execution_id} não encontrada")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao atualizar execução {execution_id}: {e}")

    @staticmethod
    def complete_execution(execution_id: str, output_data: dict, changed_by: str = None, note: str = None):
        """Marca execução como concluída com sucesso"""
        output_log = str(output_data)[:5000] if output_data else "Execução concluída"
        
        ExecutionService.update_execution_status(
            execution_id=execution_id,
            status='completed',
            output_log=output_log,
            changed_by=changed_by,
            note=note or "Execução concluída com sucesso"
        )

    @staticmethod
    def fail_execution(execution_id: str, error_message: str, changed_by: str = None, note: str = None):
        """Marca execução como falha"""
        ExecutionService.update_execution_status(
            execution_id=execution_id,
            status='failed',
            error_log=error_message[:5000] if error_message else "Erro desconhecido",
            changed_by=changed_by,
            note=note or f"Falha na execução: {error_message[:100]}"
        )

    @staticmethod
    def cancel_execution(execution_id: str, changed_by: str = None, note: str = None):
        """Cancela uma execução"""
        ExecutionService.update_execution_status(
            execution_id=execution_id,
            status='cancelled',
            changed_by=changed_by,
            note=note or "Execução cancelada pelo usuário"
        )

    # Método para consultar o histórico
    @staticmethod
    def get_execution_history(execution_id: str):
        """Retorna o histórico completo de uma execução"""
        return ExecutionStatusLog.query.filter_by(
            execution_id=execution_id
        ).order_by(ExecutionStatusLog.changed_at).all()