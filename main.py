# main.py (trecho principal)
import os
from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from APP.extensions import db
from APP.Controllers.auth_controller import auth_ns
from APP.Controllers.Automation_controller import auto_ns
import os
from pathlib import Path
from flask import Flask
from flask_cors import CORS
# from yourpkg import db, auth_ns, auto_ns  # ajuste seus imports reais

# Detecta se está no Render
ON_RENDER = os.environ.get("RENDER") == "true"

# Base do projeto (ex.: /opt/render/project/src)
BASE_DIR = Path(__file__).resolve().parent

# 1) PRIORIDADE: variável de ambiente INSTANCE_DIR (use absoluta se definir)
env_instance = os.getenv("INSTANCE_DIR")

# 2) LOCAL (Windows): se quiser manter o caminho antigo, defina LOCAL_INSTANCE_DIR na sua máquina
local_instance = os.getenv("LOCAL_INSTANCE_DIR")

# 3) Padrão: pasta 'instance' dentro do projeto (no Render é efêmera; use Render Disk se precisar persistência)
default_instance = BASE_DIR / "instance"

# Resolve a pasta levando em conta o ambiente
if env_instance:
    INSTANCE_DIR = Path(env_instance).expanduser().resolve()
elif local_instance and not ON_RENDER:
    INSTANCE_DIR = Path(local_instance).expanduser().resolve()
else:
    INSTANCE_DIR = default_instance.resolve()

# Garante que a pasta exista
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(
    __name__,
    instance_relative_config=True,
    instance_path=str(INSTANCE_DIR)  # agora é ABSOLUTO
)

# --- Banco SQLite dentro de instance ---
db_path = INSTANCE_DIR / "catalog.db"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
print("USANDO DB EM:", db_path)

# --- CORS ---
# Em produção, prefira liberar apenas o(s) domínio(s) do seu front:
allowed_origins = os.getenv("CORS_ALLOW_ORIGINS", "http://127.0.0.1:5500,http://127.0.0.1:5501,http://localhost:5500,http://localhost:5501")
CORS(
    app,
    resources={r"/*": {"origins": [o.strip() for o in allowed_origins.split(",")]}},
    supports_credentials=True
)

# --- Extensões/rotas ---
db.init_app(app)
from flask_restx import Api
api = Api(app, doc="/docs")
api.add_namespace(auth_ns, path="/auth")
api.add_namespace(auto_ns, path="/automation")

@app.get("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    with app.app_context():
        import APP.Models.models
        db.create_all()
        print("DB URL:", app.config["SQLALCHEMY_DATABASE_URI"])
        print("instance_path:", app.instance_path)
        print("URL MAP:", app.url_map)
    app.run(host="0.0.0.0", port=5000, debug=True)
