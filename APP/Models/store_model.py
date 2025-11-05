from datetime import datetime
from APP.Config.supa_config import db
from APP.Models.store_model import Store

class Store(db.Model):
    __tablename__ = "store"
    id = db.Column(db.Text, primary_key=True)
    cnpj = db.Column(db.Text, unique=True, nullable=False)
    name = db.Column(db.Text, nullable=False)
    username = db.Column(db.Text, unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.text("true"))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())