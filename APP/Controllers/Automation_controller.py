from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from APP.extensions import db
from APP.Models.models import Sector, Automation, Run
from APP.Services.teste_selenium import SeleniumTest

auto_ns = Namespace("automation", description="Catálogo de setores, automações e execuções")

# ===== Swagger models =====
sector_model = auto_ns.model("Sector", {
    "id":   fields.String(required=True),
    "name": fields.String(required=True),
})

automation_input = auto_ns.model("AutomationInput", {
    "key":         fields.String,
    "label":       fields.String,
    "type":        fields.String,
    "required":    fields.Boolean,
    "placeholder": fields.String,
})

automation_model = auto_ns.model("Automation", {
    "id":          fields.String(required=True),
    "name":        fields.String(required=True),
    "description": fields.String,
    "tags":        fields.List(fields.String),
    "inputs":      fields.List(fields.Nested(automation_input)),
})

run_model = auto_ns.model("Run", {
    "runId":        fields.Integer,
    "automationId": fields.String,
    "status":       fields.String,
    "startedAt":    fields.String,
    "finishedAt":   fields.String,
    "output":       fields.Raw,
})

# ===== /sectors =====
@auto_ns.route("/sectors")
class Sectors(Resource):
    @auto_ns.marshal_list_with(sector_model, code=200)
    def get(self):
        try:
            rows = Sector.query.order_by(Sector.name.asc()).all()
            return [{"id": s.id, "name": s.name} for s in rows], 200
        except Exception as e:
            current_app.logger.exception("Falha em GET /automation/sectors: %s", e)
            return {"message": "internal_error"}, 500

# ===== /automations =====
@auto_ns.route("/automations")
class Automations(Resource):
    @auto_ns.marshal_list_with(automation_model, code=200)
    def get(self):
        try:
            sector_id = request.args.get("sectorId")  # string
            q = Automation.query
            if sector_id:
                q = q.filter(Automation.sector_id == sector_id)

            rows = q.order_by(Automation.name.asc()).all()
            def to_dict(a: Automation):
                # Se tiver relationships, popular aqui
                return {
                    "id": a.id,
                    "name": a.name,
                    "description": a.description or "",
                    "tags": [],
                    "inputs": [],
                }
            return [to_dict(a) for a in rows], 200
        except Exception as e:
            current_app.logger.exception("Falha em GET /automation/automations: %s", e)
            return {"message": "internal_error"}, 500

# ===== /automations/<id>/run =====
@auto_ns.route("/automations/<string:automation_id>/run")
class RunAutomation(Resource):
    @auto_ns.marshal_with(run_model, code=202)
    def post(self, automation_id: str):
        try:
            run = Run(automation_id=automation_id, status="queued")
            db.session.add(run)
            db.session.commit()
            return {
                "runId": run.id,
                "automationId": run.automation_id,
                "status": run.status,
                "startedAt": run.started_at.isoformat() if getattr(run, "started_at", None) else None,
                "finishedAt": run.finished_at.isoformat() if getattr(run, "finished_at", None) else None,
                "output": run.output,
            }, 202
        except Exception as e:
            current_app.logger.exception("Falha em POST /automation/automations/%s/run: %s", automation_id, e)
            return {"message": "internal_error"}, 500

# ===== /runs (histórico) =====
@auto_ns.route("/runs")
class RunsHistory(Resource):
    @auto_ns.marshal_list_with(run_model, code=200)
    def get(self):
        rows = Run.query.order_by(Run.started_at.desc()).all()
        return [{
            "runId": r.id,
            "automationId": r.automation_id,
            "status": r.status,
            "startedAt": r.started_at.isoformat() if r.started_at else None,
            "finishedAt": r.finished_at.isoformat() if r.finished_at else None,
            "output": r.output,
        } for r in rows], 200

# ===== /runs/<id> =====
@auto_ns.route("/runs/<int:run_id>")
class RunStatus(Resource):
    @auto_ns.marshal_with(run_model, code=200)
    def get(self, run_id: int):
        r = Run.query.get(run_id)
        if not r:
            return {"message": "Run não encontrada"}, 404
        return {
            "runId": r.id,
            "automationId": r.automation_id,
            "status": r.status,
            "startedAt": r.started_at.isoformat() if r.started_at else None,
            "finishedAt": r.finished_at.isoformat() if r.finished_at else None,
            "output": r.output,
        }, 200

@auto_ns.route("/")
class AutomationRoot(Resource):
    def get(self):
        return {"ok": True}, 200
    
auto_ns.route("/testeWebdriver")
class TesteWebdriver(Resource):
    def get(self):
        automation = SeleniumTest()
        automation.driver.get("https://www.google.com")
        return {"ok": True}, 200
