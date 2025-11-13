from http import HTTPStatus
from flask import current_app, request
from flask_restx import Namespace, fields
from sqlalchemy.exc import SQLAlchemyError
from APP.Config.supa_config import db
from APP.protected_resource import ProtectedResource
from APP.Models.sector_model import Sector
from APP.Models.automation_model import Automation
from flask_restx import reqparse
from werkzeug.datastructures import FileStorage
from APP.Models.execution_status_log_model import ExecutionStatusLog
from sqlalchemy import desc
from APP.Models.executions_model import Execution 


auto_ns = Namespace("toFront", description="Catálogo de setores, automações e execuções", ordered=True)

# ==== MODELS RESTX (apenas campos que você realmente expõe) ====
sector_model = auto_ns.model("Sector", {
    "id":   fields.String(required=True, description="ID do setor"),
    "name": fields.String(required=True, description="Nome do setor"),
})

automation_list_item = auto_ns.model("AutomationListItem", {
    "id": fields.String,
    "name": fields.String,
    "description": fields.String,
    "type": fields.String,
    "is_active": fields.Boolean,
    "department_id": fields.String,
    "created_by": fields.String,
    "updated_at": fields.String,
})

automation_list_response = auto_ns.model("AutomationListResponse", {
    "items": fields.List(fields.Nested(automation_list_item)),
    "page": fields.Integer,
    "pageSize": fields.Integer,
    "total": fields.Integer
})

run_model = auto_ns.model("Run", {
    "runId":        fields.Integer,
    "automationId": fields.String,
    "status":       fields.String,
    "startedAt":    fields.String,
    "finishedAt":   fields.String,
    "output":       fields.Raw,
})

executions_model = auto_ns.model("Execution", {
    "id": fields.Integer,
    "automation": fields.String,
    "department": fields.String,
    "status": fields.String
})

run_input_model = auto_ns.model("RunInput", {
    "lojas": fields.String(required=False),
    "url": fields.String(required=False),
    "param1": fields.String(required=False),
    "param2": fields.String(required=False),
    # Adicione outros parâmetros que suas automações podem usar
})

# NO automation_controller.py - ATUALIZE o upload_parser:

# NO automation_controller.py - ATUALIZE o upload_parser:

upload_parser = reqparse.RequestParser()
upload_parser.add_argument(
    'arquivo_excel', 
    type=FileStorage, 
    location='files', 
    required=False,  # ← Agora opcional
    help='Arquivo Excel (opcional para algumas automações)'
)
upload_parser.add_argument(
    'lojas', 
    type=str, 
    location='form', 
    required=False,
    action='split',
    help='Lista de lojas para processar (opcional)'
)
upload_parser.add_argument(
    'data', 
    type=str, 
    location='form', 
    required=False,
    help='Data específica para processamento (opcional)'
)
upload_parser.add_argument(
    'url', 
    type=str, 
    location='form', 
    required=False,
    help='URL para acessar (opcional)'
)
upload_parser.add_argument(
    'pasta_destino', 
    type=str, 
    location='form', 
    required=False,
    help='Pasta de destino para downloads (opcional)'
)
upload_parser.add_argument(
    'data_inicio', 
    type=str, 
    location='form', 
    required=False,
    help='Data de início do período (opcional)'
)
upload_parser.add_argument(
    'data_fim', 
    type=str, 
    location='form', 
    required=False,
    help='Data de fim do período (opcional)'
)
upload_parser.add_argument(
    'filial', 
    type=str, 
    location='form', 
    required=False,
    help='Filial específica (opcional)'
)
upload_parser.add_argument(
    'modo', 
    type=str, 
    location='form', 
    required=False,
    help='Modo de execução (opcional)'
)
# Adicione outros parâmetros conforme necessário

# ===== /automation/departments ===== (NÃO use jsonify aqui)
@auto_ns.route("/departments")
class Departments(ProtectedResource):  # use ProtectedResource se quiser JWT aqui
    @auto_ns.marshal_list_with(sector_model, code=HTTPStatus.OK, envelope=None)
    def get(self):
        try:
            # pegue somente as colunas necessárias e converta para dict simples
            rows = db.session.query(Sector.id, Sector.name).filter(Sector.is_active == True)
            data = [{"id": str(i), "name": n} for (i, n) in rows]
            current_app.logger.info("[DEPARTMENTS] %d registros", len(data))
            return data, HTTPStatus.OK
        except Exception:
            current_app.logger.exception("[DEPARTMENTS] Erro")
            db.session.rollback()
            auto_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Internal Server Error")

# ===== /automation/automations/<department_id> =====
@auto_ns.route("/automations/<string:department_id>")

class Automations(ProtectedResource):  # use ProtectedResource se exigir JWT
    @auto_ns.marshal_with(automation_list_response, code=HTTPStatus.OK, envelope=None)
    def get(self, department_id: str):
        try:
            rows = (Automation.query
                    .filter(Automation.department_id == department_id,
                    Automation.is_active == True)
                    .order_by(Automation.name)
                    .all())

            items = []
            for a in rows:
                if getattr(a, "is_active", False):
                    items.append({
                        "id": str(a.id),
                        "name": a.name,
                        "description": a.description,
                        "type": getattr(a, "type", None),
                        "is_active": bool(a.is_active),
                        "department_id": str(a.department_id) if getattr(a, "department_id", None) is not None else None,
                        "created_by": getattr(a, "created_by", None),
                        "updated_at": a.updated_at.isoformat() if getattr(a, "updated_at", None) else None,
                    })

            resp = {
                "items": items,
                "page": 1,
                "pageSize": len(items),
                "total": len(items)
            }
            return resp, HTTPStatus.OK

        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("[AUTOMATIONS] Erro de banco")
            auto_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Internal Server Error")
        except Exception:
            current_app.logger.exception("[AUTOMATIONS] Erro inesperado")
            auto_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Internal Server Error")


        
# ===== /automation/ (ping) =====
automation_model = auto_ns.model("Automation", {
    "id":          fields.String(required=True),
    "name":        fields.String(required=True),
    "description": fields.String,
})


@auto_ns.route("/")
class AutomationRoot(ProtectedResource):
    @auto_ns.marshal_list_with(automation_model, code=HTTPStatus.OK, envelope=None)
    def get(self):
        # pegue só as colunas que vai expor
        rows = db.session.query(Automation.id, Automation.name, Automation.description)\
                         .limit(5).all()
        data = [{"id": str(i), "name": n, "description": d} for (i, n, d) in rows]
        current_app.logger.info("[AUTOMATIONS] Amostra IDs: %s", [d["id"] for d in data])
        return data, HTTPStatus.OK

@auto_ns.route("/status/<string:department_id>/<string:automation_id>/<string:user_id>")
class AutomationStatus(ProtectedResource):
    def get(self, department_id: str, automation_id: str, user_id: str):
        try:
            print(f"🔍 Buscando status: department={department_id}, automation={automation_id}")
            
            # Busca a ÚLTIMA execução específica
            results = (
                db.session.query(ExecutionStatusLog, Execution)
                .join(Execution, ExecutionStatusLog.execution_id == Execution.id)
                .filter(
                    ExecutionStatusLog.changed_by == user_id,
                    Execution.automation_id == automation_id  # ← ADICIONE ESTE FILTRO IMPORTANTE
                )
                .order_by(desc(ExecutionStatusLog.changed_at))
                .first()  # ← Mude para first() para pegar apenas o mais recente
            )
            
            if results:
                status_log, execution = results  # ← Desempacota a tupla
                print(f"✅ Última execução encontrada: {execution.status}")
                
                return {
                    "department_id": department_id,
                    "automation_id": automation_id,
                    "automation_name": execution.automation.name if hasattr(execution, 'automation') and execution.automation else "N/A",
                    "status": execution.status,
                    "last_updated": status_log.changed_at.isoformat() if status_log.changed_at else None,
                    "changed_by": status_log.changed_by
                }, HTTPStatus.OK
            else:
                print(f"⚠️  Nenhuma execução encontrada para {automation_id}")
                
                return {
                    "department_id": department_id,
                    "automation_id": automation_id,
                    "status": "never_executed",
                    "message": "Esta automação nunca foi executada"
                }, HTTPStatus.OK
                
        except Exception as e:
            print(f"❌ Erro ao buscar status: {e}")
            db.session.rollback()
            return {"error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
    

@auto_ns.route("/historico")
class HistoricoList(ProtectedResource):
    def get(self):
        """Busca histórico simples de execuções DO USUÁRIO LOGADO"""
        try:
            # Pega o username do LDAP do token JWT
            from flask_jwt_extended import get_jwt_identity
            
            username_ldap = get_jwt_identity()  # Este é o username do LDAP
            if not username_ldap:
                return {"error": "Usuário não autenticado"}, HTTPStatus.UNAUTHORIZED
            
            print(f"📊 Buscando histórico para usuário LDAP: {username_ldap}")
            
            pagina = request.args.get('pagina', 1, type=int)
            limite = request.args.get('limite', 20, type=int)
            status = request.args.get('status', None)
            automation_id = request.args.get('automation_id', None)
            
            # Query base - FILTRANDO PELO USERNAME DO LDAP
            query = db.session.query(
                Execution, 
                Automation.name.label('automation_name'),
                ExecutionStatusLog.changed_by.label('user_id')
            )
            query = query.join(Automation, Execution.automation_id == Automation.id)
            query = query.join(ExecutionStatusLog, Execution.id == ExecutionStatusLog.execution_id)
            
            # FILTRO PRINCIPAL: apenas execuções do usuário LDAP logado
            query = query.filter(ExecutionStatusLog.changed_by == username_ldap)
            
            # Filtros adicionais
            if status:
                query = query.filter(Execution.status == status)
            if automation_id:
                query = query.filter(Execution.automation_id == automation_id)
            
            # Paginação - PEGA APENAS O ÚLTIMO STATUS LOG POR EXECUÇÃO
            subquery = db.session.query(
                ExecutionStatusLog.execution_id,
                db.func.max(ExecutionStatusLog.changed_at).label('max_changed_at')
            ).group_by(ExecutionStatusLog.execution_id).subquery()
            
            historico = query.join(
                subquery, 
                db.and_(
                    ExecutionStatusLog.execution_id == subquery.c.execution_id,
                    ExecutionStatusLog.changed_at == subquery.c.max_changed_at
                )
            ).order_by(desc(Execution.created_at))\
             .offset((pagina - 1) * limite)\
             .limit(limite)\
             .all()
            
            dados = []
            for execucao, automation_name, user_id in historico:
                dados.append({
                    "id": execucao.id,
                    "automation_name": automation_name,
                    "status": execucao.status,
                    "started_by": user_id,  # Este será o username LDAP
                    "start_time": execucao.start_time.isoformat() if execucao.start_time else None,
                    "end_time": execucao.end_time.isoformat() if execucao.end_time else None,
                    "exit_code": execucao.exit_code,
                    "created_at": execucao.created_at.isoformat() if execucao.created_at else None
                })
            
            return {
                "pagina": pagina,
                "limite": limite,
                "total_encontrado": len(dados),
                "usuario_logado": username_ldap,  # Para debug
                "dados": dados
            }, HTTPStatus.OK
            
        except Exception as e:
            print(f"❌ Erro ao buscar histórico: {e}")
            return {"error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR