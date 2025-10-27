from datetime import datetime
from APP.Config.supa_config import db

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Text, primary_key=True)
    email = db.Column(db.Text, unique=True, nullable=False)
    username = db.Column(db.Text, unique=True, nullable=False)
    hashed_password = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.text("true"))
    is_superuser = db.Column(db.Boolean, nullable=False, server_default=db.text("false"))
    department_id = db.Column(db.Text, db.ForeignKey("departments.id"))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
