# APP/Models/sector.py
from APP.Config.supa_config import db

class Sector(db.Model):
    __tablename__ = "departments"  # mapeia seu DDL de departments
    id = db.Column(db.Text, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    code = db.Column(db.Text, unique=True, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.text("true"))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
