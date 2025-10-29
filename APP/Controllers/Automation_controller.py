from http import HTTPStatus
from flask import current_app, request, session
from flask_restx import Namespace, Resource, fields
from numpy import append
from APP.Models.run_model import Run
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_  
from APP.Config.supa_config import db
from APP.protected_resource import ProtectedResource 
from APP.Models.sector_model import  Sector
from APP.Models.automation_model import Automation
from APP.Models.run_model import Run

auto_ns = Namespace("automation", description="Catálogo de setores, automações e execuções")

sector_model = auto_ns.model("Sector", {
    "id":   fields.String(required=True, description="ID do setor"),
    "name": fields.String(required=True, description="Nome do setor"),
})

automation_input = auto_ns.model("AutomationInput", {
    "key":         fields.String(description="Chave do input"),
    "label":       fields.String(description="Rótulo"),
    "type":        fields.String(description="Tipo de campo"),
    "required":    fields.Boolean(description="É obrigatório?"),
    "placeholder": fields.String(description="Placeholder"),
})

automation_model = auto_ns.model("Automation", {
    "id":          fields.String(required=True, description="ID"),
    "name":        fields.String(required=True, description="Nome"),
    "description": fields.String(description="Descrição"),
    "tags":        fields.List(fields.String, description="Tags"),
    "inputs":      fields.List(fields.Nested(automation_input), description="Schema de inputs"),
})

run_model = auto_ns.model("Run", {
    "runId":        fields.Integer(description="ID da execução"),
    "automationId": fields.String(description="ID da automação"),
    "status":       fields.String(description="Status da execução"),
    "startedAt":    fields.String(description="Início (ISO8601)"),
    "finishedAt":   fields.String(description="Fim (ISO8601)"),
    "output":       fields.Raw(description="Saída da automação"),
})
automation_list_item = auto_ns.model("AutomationListItem", {
    "id": fields.String,
    "name": fields.String,
    "description": fields.String,
    "type": fields.String,
    "is_active": fields.Boolean,
    "department_id": fields.String,
    "created_by": fields.String,
    "updated_at": fields.String,  # No seu model é updated_at (DateTime)
})
automation_list_response = auto_ns.model("AutomationListResponse", {
    "items": fields.List(fields.Nested(automation_list_item)),
    "page": fields.Integer,
    "pageSize": fields.Integer,
    "total": fields.Integer
})

# ===== /automation/sectors =====
@auto_ns.route("/departments")
class Sectors(ProtectedResource):
    @auto_ns.marshal_list_with(sector_model, code=HTTPStatus.OK)
    def get(self):
        try:
            sectors = (
                Sector.query
                .execution_options(populate_existing=True)
                .all()
            )
            current_app.logger.info("[DEPARTMENTS] %d registros retornados", len(sectors))
            return sectors, HTTPStatus.OK

        except Exception as e:
            current_app.logger.exception("[DEPARTMENTS] Erro ao listar: %s", e)
            # GET normalmente não altera estado, mas se algo abriu transação, garante rollback
            try:
                db.session.rollback()
            except Exception:
                pass
            return {"message": "internal_error"}, HTTPStatus.INTERNAL_SERVER_ERROR

# ===== /automation/automations =====
@auto_ns.route("/automations/<string:department_id>")
class Automations(ProtectedResource):
    @auto_ns.response(HTTPStatus.OK, 'Success', automation_list_response)
    def get(self, department_id: str):
        try:
            automations = (
                Automation.query
                .filter(Automation.department_id == department_id)  # ✅ CORRIGIDO
                .execution_options(populate_existing=True)
                .all()
            )
            
            current_app.logger.info(
                "[AUTOMATIONS] %d registros retornados para department_id=%s",
                len(automations),
                department_id
            )
            
 
            items = []
            for automation in automations:
                if automation.is_active:
                    items.append({
                    "name": automation.name,
                    })
            
            response = {
                "items": items,
                "page": 1,
                "pageSize": len(items),
                "total": len(items)
            }
            
            return response, HTTPStatus.OK
            
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.exception(
                "[AUTOMATIONS] Erro de banco em GET /automations/%s: %s",
                department_id,
                e
            )
            auto_ns.abort(500, "Internal Server Error")
        except Exception as e:
            current_app.logger.exception(
                "[AUTOMATIONS] Erro inesperado em GET /automations/%s: %s",
                department_id,
                e
            )
            auto_ns.abort(500, "Internal Server Error")

@auto_ns.route("/automations/<string:automation_id>/run")
class RunAutomation(ProtectedResource):
    @auto_ns.marshal_with(run_model, code=HTTPStatus.ACCEPTED)
    def post(self, automation_id: str):
        try:
            run = run(automation_id=automation_id, status="queued")
            db.session.add(run)
            db.session.commit()

            return {
                "runId": run.id,
                "automationId": run.automation_id,
                "status": run.status,
                "startedAt": run.started_at.isoformat() if getattr(run, "started_at", None) else None,
                "finishedAt": run.finished_at.isoformat() if getattr(run, "finished_at", None) else None,
                "output": run.output,
            }, HTTPStatus.ACCEPTED
        except Exception as e:
            current_app.logger.exception("Falha em POST /automation/automations/%s/run: %s", automation_id, e)
            return {"message": "internal_error"}, HTTPStatus.INTERNAL_SERVER_ERROR

# ===== /automation/runs (histórico) =====
@auto_ns.route("/runs")
class RunsHistory(ProtectedResource):
    @auto_ns.marshal_list_with(run_model, code=HTTPStatus.OK)
    def get(self):
        rows = Run.query.order_by(Run.started_at.desc()).all()
        return [{
            "runId": r.id,
            "automationId": r.automation_id,
            "status": r.status,
            "startedAt": r.started_at.isoformat() if r.started_at else None,
            "finishedAt": r.finished_at.isoformat() if r.finished_at else None,
            "output": r.output,
        } for r in rows], HTTPStatus.OK

# ===== /automation/runs/<id> =====
@auto_ns.route("/runs/<int:run_id>")
class RunStatus(ProtectedResource):
    @auto_ns.marshal_with(run_model, code=HTTPStatus.OK)
    def get(self, run_id: int):
        r = Run.query.get(run_id)
        if not r:
            return {"message": "Run não encontrada"}, HTTPStatus.NOT_FOUND
        return {
            "runId": r.id,
            "automationId": r.automation_id,
            "status": r.status,
            "startedAt": r.started_at.isoformat() if r.started_at else None,
            "finishedAt": r.finished_at.isoformat() if r.finished_at else None,
            "output": r.output,
        }, HTTPStatus.OK

# ===== /automation/ (ping) =====
@auto_ns.route("/")
class AutomationRoot(ProtectedResource):
    @auto_ns.marshal_list_with(automation_model, code=HTTPStatus.OK)
    def get(self):
        items = Automation.query.limit(5).all()
        current_app.logger.info("[AUTOMATIONS] Amostra sem filtro: %s", [a.id for a in items])
        # ✅ retorne a própria lista de modelos; o marshal serializa
        return items, HTTPStatus.OK
