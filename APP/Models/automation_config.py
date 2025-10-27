from datetime import datetime
from APP.Config.supa_config import db

class AutomationConfig(db.Model):
    __tablename__ = "automation_configs"
    id = db.Column(db.Text, primary_key=True)
    automation_id = db.Column(db.Text, db.ForeignKey("automations.id", ondelete="CASCADE"))
    config_key = db.Column(db.Text, nullable=False)
    config_value = db.Column(db.Text)
    config_type = db.Column(db.Text, nullable=False, server_default=db.text("'string'"))  # 'string','number','boolean','json'
    is_secret = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    automation = db.relationship("Automation", lazy="joined")