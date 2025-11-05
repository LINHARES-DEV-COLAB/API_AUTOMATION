# APP/Models/automation_model.py - ATUALIZADO
from APP.Config.supa_config import db

class Automation(db.Model):
    __tablename__ = "automations"
    id = db.Column(db.Text, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    script_path = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text, nullable=False)  # 'fidc' | 'baixas_pan' | 'outra_automacao'
    schedule_cron = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.text("true"))
    max_execution_time = db.Column(db.Integer, nullable=False, server_default=db.text("3600"))
    created_by = db.Column(db.Text, db.ForeignKey("users.id"))
    department_id = db.Column(db.Text, db.ForeignKey("departments.id"))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())