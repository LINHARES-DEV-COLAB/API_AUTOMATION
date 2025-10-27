# APP/Models/run.py
from datetime import datetime
from APP.Config.supa_config import db

class Run(db.Model):
    __tablename__ = "runs"  # use "executions" se você preferir unificar
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    automation_id = db.Column(db.Text, nullable=False, index=True)
    status = db.Column(db.String(32), nullable=False, default="queued")
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    output = db.Column(db.JSON, nullable=True)
