from flask import current_app
from flask_restx import Namespace, Resource, fields
from http import HTTPStatus

from APP.common.protected_resource import ProtectedResource
from APP.Models.automation_model import Automation
from APP.Config.supa_config import db  # ✅ Importar db para session
from APP.Services.fidc_service import run as run_fidc_service

fidc_ns = Namespace('fidc', description='Emissão de boletos para as montadoreas via FIDC')

fidc_response_model = fidc_ns.model('FIDCResponse', {
    'status': fields.String(description='Status da execução'),
    'message': fields.String(description='Mensagem detalhada')
})

@fidc_ns.route('/fidc')
class FIDCController(ProtectedResource):
    @fidc_ns.marshal_with(fidc_response_model)
    def get(self):
        try:
            automation_id = "fidc"
            db.session.expire_all() 
            automation = Automation.query.filter_by(id=automation_id).first()
            
            if automation:
                # ✅ Força recarregamento do objeto específico
                db.session.refresh(automation)
            
            if not automation:
                return {
                    'status': 'error',
                    'message': f'Automação FIDC não encontrada'
                }, HTTPStatus.NOT_FOUND
            
            # 🔍 DEBUG EXTRA
            current_app.logger.info(f"🎯 Valor do is_active: {automation.is_active}")
            
            # ✅ Verificação EXPLÍCITA
            if automation.is_active == False or automation.is_active == 0:
                current_app.logger.info("❌ Automação DESATIVADA - bloqueando execução")
                return {
                    'status': 'error',
                    'message': f'Automação FIDC está desativada (valor: {automation.is_active})'
                }, HTTPStatus.FORBIDDEN
            
            # Executa o serviço
            result = run_fidc_service()
            
            if result:
                return {
                    'status': 'success',
                    'message': 'FIDC executado com sucesso'
                }, HTTPStatus.OK
            else:
                return {
                    'status': 'error',
                    'message': 'Falha ao executar serviço FIDC'
                }, HTTPStatus.INTERNAL_SERVER_ERROR
            
        except Exception as e:
            current_app.logger.exception("Erro em GET /fidc/fidc: %s", e)
            return {
                'status': 'error',
                'message': f'Erro ao executar FIDC: {str(e)}'
            }, HTTPStatus.INTERNAL_SERVER_ERROR