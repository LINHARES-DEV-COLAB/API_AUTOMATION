import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    uri = os.getenv("DATABASE_URL")
    assert uri, "DATABASE_URL não configurada"
    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Pools (opcional, bom para Render + pgbouncer)
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": int(os.getenv("SQLALCHEMY_POOL_SIZE", 5)),
        "max_overflow": int(os.getenv("SQLALCHEMY_MAX_OVERFLOW", 10)),
        "pool_recycle": int(os.getenv("SQLALCHEMY_POOL_RECYCLE", 1800)),
    }
    db.init_app(app)
