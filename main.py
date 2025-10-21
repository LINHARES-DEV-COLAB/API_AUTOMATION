# main.py
from datetime import timedelta
import os
from pathlib import Path
from flask import Flask, redirect, jsonify, request 
from flask_cors import CORS
from flask_restx import Api
from flask_jwt_extended import JWTManager
from APP.extensions_service import db
from APP.Controllers.auth_controller import auth_ns
from APP.Controllers.solicitacao_carga_route import solicitacao_carga_ns



BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = Path(os.getenv("INSTANCE_DIR", BASE_DIR / "instance")).resolve()
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = INSTANCE_DIR / "catalog.db"



def create_app():
    app = Flask(__name__, instance_relative_config=True, instance_path=str(INSTANCE_DIR))

    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY" , "")    
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=int(os.getenv("JWT_EXPIRE_MIN", "30")))
    jwt = JWTManager(app)

    authorizations = {
        "Bearer Auth": {
            "type":"apiKey",
            "in":"header",
            "name":"Authorization",
            "description":"Use: Bearer <token>"
        }
    }

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ECHO"] = True

    db.init_app(app)

    api = Api(app, doc="/docs", title="Automations API", version="1.0", authorizations=authorizations, security="Bearer Auth")

    api.add_namespace(auth_ns, path="/auth")
    api.add_namespace(solicitacao_carga_ns, path="/solicitacao-carga")

    CORS(
        app,
        resources={r"/*": {"origins": ["http://127.0.0.1:5500", "http://localhost:5500"]}},
        supports_credentials=True,
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    @app.get("/", endpoint="index_redirect")
    def index_redirect():
        return redirect("/docs", code=302)

    # with app.app_context():
    #     from APP.Models.base_models import Sector, Automation, Run  # noqa: F401

    #     db.create_all()

    #     if os.getenv("SEED_ON_START") == "1":
    #         try:
    #             from APP.Data.seed_db import run_seed
    #             run_seed()
    #         except Exception as e:
    #             app.logger.exception("Seed falhou: %s", e)

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", "10000"))
    # app.run(port=8980, host="172.17.67.19")
    app.run(port=5000, host="0.0.0.0")


