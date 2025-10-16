from flask import Blueprint, request, jsonify
from datetime import datetime
from APP.extensions_service import db
from APP.Models.base_models import Run, Automation
from APP.Services.catalog import list_sectors, list_automations, get_automation

auto_bp = Blueprint("auto_bp", __name__)

@auto_bp.get("/sectors")
def sectors():
    return jsonify(list_sectors()), 200

@auto_bp.get("/automations")
def automations():
    sector_id = request.args.get("sectorId")
    return jsonify(list_automations(sector_id)), 200

@auto_bp.post("/automations/<automation_id>/run")
def run_automation(automation_id: str):
    data = request.get_json(silent=True) or {}
    payload = data.get("payload") or {}

    # valida automação e campos obrigatórios
    a = get_automation(automation_id)
    if not a:
        return jsonify({"error": "Automação não encontrada"}), 404
    missing = [i["label"] for i in a.get("inputs", [])
               if i.get("required") and not str(payload.get(i["key"], "")).strip()]
    if missing:
        return jsonify({"error": f"Preencha: {', '.join(missing)}"}), 400

    # cria run no banco
    run = Run(automation_id=automation_id, status="running", started_at=datetime.utcnow())
    db.session.add(run)
    db.session.commit()

    # TODO: executar de verdade; mock de finalização:
    run.status = "succeeded"
    run.finished_at = datetime.utcnow()
    run.output = "Execução concluída (mock)."
    db.session.commit()

    return jsonify({"runId": run.id, "status": run.status, "startedAt": run.started_at.isoformat()}), 202

@auto_bp.get("/runs/<int:run_id>")
def run_status(run_id: int):
    run = Run.query.get(run_id)
    if not run:
        return jsonify({"error": "Run não encontrada"}), 404
    return jsonify({
        "runId": run.id,
        "automationId": run.automation_id,
        "status": run.status,
        "startedAt": run.started_at.isoformat(),
        "finishedAt": run.finished_at.isoformat() if run.finished_at else None,
        "output": run.output
    }), 200

@auto_bp.get("/runs/recent")
def runs_recent():
    items = Run.query.order_by(Run.started_at.desc()).limit(10).all()
    return jsonify([{
        "runId": r.id,
        "automationId": r.automation_id,
        "status": r.status,
        "startedAt": r.started_at.isoformat(),
        "finishedAt": r.finished_at.isoformat() if r.finished_at else None
    } for r in items]), 200
