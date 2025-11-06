from datetime import datetime
from APP.Config.supa_config import db

class ExecutionStatusLog(db.Model):
    __tablename__ = 'execution_status_log'
    
    id = db.Column(db.Text, primary_key=True)
    execution_id = db.Column(db.Text, db.ForeignKey('executions.id'), nullable=False)
    status_before = db.Column(db.Text)
    status_after = db.Column(db.Text, nullable=False)
    note = db.Column(db.Text)
    changed_by = db.Column(db.Text)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)