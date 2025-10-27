from datetime import datetime
from APP.Config.supa_config import db

class Execution(db.Model):
    __tablename__ = "executions"
    id = db.Column(db.Text, primary_key=True)
    automation_id = db.Column(db.Text, db.ForeignKey("automations.id", ondelete="CASCADE"))
    triggered_by = db.Column(db.Text, db.ForeignKey("users.id"))
    status = db.Column(db.Text, nullable=False, server_default=db.text("'pending'"))
    start_time = db.Column(db.DateTime(timezone=True))
    end_time = db.Column(db.DateTime(timezone=True))
    exit_code = db.Column(db.Integer)
    output_log = db.Column(db.Text)
    error_log = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    automation = db.relationship("Automation", lazy="joined")
    trigger_user = db.relationship("User", foreign_keys=[triggered_by], lazy="joined")