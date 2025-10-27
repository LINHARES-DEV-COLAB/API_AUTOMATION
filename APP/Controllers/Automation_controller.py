from http import HTTPStatus
from flask import current_app, request
from flask_restx import Namespace, Resource, fields
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
    "id":          fields.String,
    "name":        fields.String,
    "description": fields.String,
    "type":        fields.String,
    "is_active":   fields.Boolean,
    "department_id": fields.String,
    "created_by":  fields.String,
    "updated_at":  fields.String,
})
automation_list_response = auto_ns.model("AutomationListResponse", {
    "items": fields.List(fields.Nested(automation_list_item)),
    "page": fields.Integer,
    "pageSize": fields.Integer,
    "total": fields.Integer
})

# ===== /automation/sectors =====
@auto_ns.route("/sectors")
class Sectors(ProtectedResource):
    @auto_ns.marshal_list_with(sector_model, code=HTTPStatus.OK)
    def get(self):
        try:
            rows = Sector.query.order_by(Sector.name.asc()).all()
            return [{"id": s.id, "name": s.name} for s in rows], HTTPStatus.OK
        except Exception as e:
            current_app.logger.exception("Falha em GET /automation/sectors: %s", e)
            return {"message": "internal_error"}, HTTPStatus.INTERNAL_SERVER_ERROR

# ===== /automation/automations =====
@auto_ns.route("/automations")
class Automations(ProtectedResource):
    @auto_ns.marshal_with(automation_list_response, code=HTTPStatus.OK)
    @auto_ns.response(401, "Unauthorized")
    @auto_ns.response(500, "Internal Server Error")
    def get(self):
        """
        Lista automações com filtros:
          - departmentId: str
          - type: 'manual' | 'scheduled' | 'triggered'
          - isActive: '0' ou '1'
          - q: busca textual (name/description)
          - page, pageSize: paginação
        """
        try:
            # --- filtros ---
            dept_id  = request.args.get("departmentId")
            type_    = request.args.get("type")  # 'manual'|'scheduled'|'triggered'
            is_active_param = request.args.get("isActive")  # '0' ou '1'
            q        = (request.args.get("q") or "").strip()

            # --- paginação ---
            try:
                page = max(int(request.args.get("page", 1)), 1)
            except ValueError:
                page = 1
            try:
                page_size = min(max(int(request.args.get("pageSize", 20)), 1), 200)
            except ValueError:
                page_size = 20
            offset = (page - 1) * page_size

            query = Automation.query

            if dept_id:
                query = query.filter(Automation.department_id == dept_id)
            if type_:
                query = query.filter(Automation.type == type_)
            if is_active_param in ("0", "1"):
                query = query.filter(Automation.is_active == (is_active_param == "1"))
            if q:
                like = f"%{q}%"
                query = query.filter(or_(Automation.name.ilike(like),
                                         Automation.description.ilike(like)))

            total = query.count()
            rows = (query.order_by(Automation.name.asc())
                         .offset(offset)
                         .limit(page_size)
                         .all())

            def to_item(a: Automation):
                return {
                    "id": a.id,
                    "name": a.name,
                    "description": a.description or "",
                    "type": a.type,
                    "is_active": bool(a.is_active),
                    "department_id": a.department_id,
                    "created_by": a.created_by,
                    "updated_at": a.updated_at.isoformat() if getattr(a, "updated_at", None) else None,
                }

            return {
                "items":    [to_item(a) for a in rows],
                "page":     page,
                "pageSize": page_size,
                "total":    total
            }, HTTPStatus.OK

        except SQLAlchemyError as e:
            current_app.logger.exception("DB error em GET /automation/automations: %s", e)
            auto_ns.abort(500, "Internal Server Error")
        except Exception as e:
            current_app.logger.exception("Erro em GET /automation/automations: %s", e)
            auto_ns.abort(500, "Internal Server Error")

# ===== /automation/automations/<id>/run =====
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
    def get(self):
        return {"ok": True}, HTTPStatus.OK
