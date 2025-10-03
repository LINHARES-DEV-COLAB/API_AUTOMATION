# main.py
import os
from pathlib import Path
from flask import Flask, redirect
from flask_cors import CORS
from flask_restx import Api
from APP.Controllers.controller_teste import selenium_ns
from APP.extensions import db
from APP.Controllers.auth_controller import auth_ns
from APP.Controllers.Automation_controller import auto_ns

# Instance dir absoluto
BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = Path(os.getenv("INSTANCE_DIR", BASE_DIR / "instance")).resolve()
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, instance_relative_config=True, instance_path=str(INSTANCE_DIR))

# Config DB
db_path = INSTANCE_DIR / "catalog.db"

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True  # TEMP: loga as queries

# Inicializa extensões ANTES de usar
db.init_app(app)

# RESTX
api = Api(app, doc="/docs", title="Automations API", version="1.0")
api.add_namespace(auth_ns, path="/auth")
api.add_namespace(auto_ns, path="/automation")
api.add_namespace(selenium_ns, path="/teste")
# CORS (ajuste origens)
CORS(app, resources={r"/*": {"origins": ["http://127.0.0.1:5500","http://localhost:5500"]}},
     supports_credentials=True)

@app.get("/health")
def health():
    return {"status": "ok"}, 200

@app.get("/", endpoint="index_redirect")
def index_redirect():
    return redirect("/docs", code=302)

# >>> Criação de tabelas: precisa dos MODELS carregados <<<
with app.app_context():
    # importe os models DEPOIS de init_app e DENTRO do app_context
    from APP.Models.models import Sector, Automation, Run  # noqa: F401
    db.create_all()

    # Opcional: seed idempotente
    if os.getenv("SEED_ON_START") == "1":
        try:
            from APP.Data.seed_db import run_seed
            run_seed()
        except Exception as e:
            app.logger.exception("Seed falhou: %s", e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # debug só local
