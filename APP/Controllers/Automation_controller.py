from enum import auto
from http import HTTPStatus
from pdb import run
from click import Parameter
from flask import current_app, request
from flask_restx import Namespace, Resource, fields
from sqlalchemy.exc import SQLAlchemyError
from APP.Config.supa_config import db
from APP.protected_resource import ProtectedResource
from APP.Models.sector_model import Sector
from APP.Models.automation_model import Automation
from APP.Models.run_model import Run  

auto_ns = Namespace("automation", description="Catálogo de setores, automações e execuções")

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

run_input_model = auto_ns.model("RunInput", {
    "lojas": fields.String(required=False),
    "url": fields.String(required=False),
    "param1": fields.String(required=False),
    "param2": fields.String(required=False),
    # Adicione outros parâmetros que suas automações podem usar
})

# ===== /automation/departments ===== (NÃO use jsonify aqui)
@auto_ns.route("/departments")
class Departments(Resource):  # use ProtectedResource se quiser JWT aqui
    @auto_ns.marshal_list_with(sector_model, code=HTTPStatus.OK, envelope=None)
    def get(self):
        try:
            # pegue somente as colunas necessárias e converta para dict simples
            rows = db.session.query(Sector.id, Sector.name).all()
            data = [{"id": str(i), "name": n} for (i, n) in rows]
            current_app.logger.info("[DEPARTMENTS] %d registros", len(data))
            return data, HTTPStatus.OK
        except Exception:
            current_app.logger.exception("[DEPARTMENTS] Erro")
            db.session.rollback()
            auto_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Internal Server Error")

# ===== /automation/automations/<department_id> =====
@auto_ns.route("/automations/<string:department_id>")
class Automations(Resource):  # use ProtectedResource se exigir JWT
    @auto_ns.marshal_with(automation_list_response, code=HTTPStatus.OK, envelope=None)
    def get(self, department_id: str):
        try:
            rows = (Automation.query
                    .filter(Automation.department_id == department_id)
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


@auto_ns.route("/automations/<string:automation_id>/run")
class RunAutomation(ProtectedResource):
    @auto_ns.marshal_with(run_model, code=HTTPStatus.ACCEPTED, envelope=None)
    def post(self, automation_id: str):
        try:
            # Trata requests sem Content-Type JSON
            if request.content_type and 'application/json' in request.content_type:
                parameters = request.json or {}
            else:
                parameters = {}
            
            print(f"🔍 DEBUG - Parameters: {parameters}")
            print(f"🔍 DEBUG - Chamando factory para: {automation_id}")
            
            from APP.Services.central_service import AutomationFactory
            factory = AutomationFactory()
            command = factory.create_command(automation_id)
            
            print(f"🔍 DEBUG - Command retornado: {command}")
            print(f"🔍 DEBUG - Tipo do command: {type(command)}")
            
            if not command:
                print("❌ DEBUG - Command NÃO encontrado!")
                return {"error": "Automação não encontrada"}, 404
            
            print("✅ DEBUG - Command encontrado! Validando parâmetros...")
            if not command.validate_parameters(parameters):
                return {"error": "Parâmetros inválidos"}, 400
            
            print("🚀 DEBUG - Executando command...")
            resultado = command.execute(parameters)
            print(f"🔍 DEBUG - Resultado: {resultado}")
            
            # Cria registro no banco
            r = Run(automation_id=automation_id, status="completed")
            r.output = resultado
            db.session.add(r)
            db.session.commit()
            
            return {
                "runId": r.id,
                "automationId": r.automation_id,
                "status": r.status,
                "startedAt": r.started_at.isoformat() if r.started_at else None,
                "finishedAt": r.finished_at.isoformat() if r.finished_at else None,
                "output": resultado,
            }, HTTPStatus.ACCEPTED
            
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return {"error": str(e)}, 500  # ← Use return em vez de auto_ns.abort

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
    
@auto_ns.route("/test-simple")
class TestSimple(Resource):  # ← Use Resource em vez de ProtectedResource
    def post(self):
        print("🔍 DEBUG - Rota simples funcionando!")
        return {"message": "Rota simples funciona!", "status": "success"}, 200
