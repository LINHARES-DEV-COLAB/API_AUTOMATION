# main.py (trecho principal)
import os
from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from APP.extensions import db
from APP.Controllers.auth_controller import auth_ns
from APP.Controllers.Automation_controller import auto_ns

# Caminho fixo para o instance dir
INSTANCE_DIR = r"C:\Users\sousa.lima\Documents\EstudoAPI\APP\Data\instance"
os.makedirs(INSTANCE_DIR, exist_ok=True)

app = Flask(__name__, instance_relative_config=True, instance_path=INSTANCE_DIR)

db_path = os.path.join(app.instance_path, "catalog.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
print("USANDO DB EM:", db_path)

CORS(app, resources={r"/*": {"origins": ["http://127.0.0.1:5500","http://127.0.0.1:5501","http://localhost:5500","http://localhost:5501"]}}, supports_credentials=True)

db.init_app(app)
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
