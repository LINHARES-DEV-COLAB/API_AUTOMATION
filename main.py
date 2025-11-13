from ast import Import
from concurrent.futures import thread
from datetime import timedelta
import os
from APP.Config.supa_config import init_db
from pathlib import Path
from flask import Flask, redirect, jsonify, request 
from flask_cors import CORS
from flask_restx import Api
from flask_jwt_extended import JWTManager
from APP.Controllers.auth_controller import auth_ns
from APP.Controllers.solicitacao_carga_controller import solicitacao_carga_ns
from APP.Controllers.conciliacao_cdc_honda_controller import conciliacao_cdc_honda_ns
from APP.Controllers.baixa_arquivos_cnh_controller import baixa_arquivos_cnh_honda_ns
from APP.Controllers.preparacao_baixas_controller import preparacao_baixas_ns
from APP.Controllers.abrir_driver_controller import abrir_driver_ns
from APP.Controllers.Automation_controller import auto_ns
from APP.Controllers.aymore_controller import aymore_ns
from APP.Controllers.fidc_controller import fidc_ns
from APP.Controllers.pan_controller import  pan_ns
from APP.Config.supa_config import init_db, db
from sqlalchemy import text
import logging
import os, uuid, time, threading, tempfile
from concurrent.futures import ThreadPoolExecutor

EXECUTOR = ThreadPoolExecutor(max_workers=4)
BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"             # <- define
INSTANCE_DIR.mkdir(parents=True, exist_ok=True) 

def create_app(test_config=None):

    app = Flask(__name__, 
                instance_relative_config=True, 
            instance_path=str(INSTANCE_DIR))
    
    class ExecutionStore:
        def __init__(self):
            self._lock = threading.Lock()
            self._data = {}  # exec_id -> dict

        def create(self):
            exec_id = str(uuid.uuid4())
            with self._lock:
                self._data[exec_id] = {
                    "status": "queued",
                    "logs": [],
                    "started_at": None,
                    "finished_at": None,
                    "output": None,
                    "error": None,
                }
            return exec_id

        def set(self, exec_id, **fields):
            with self._lock:
                if exec_id in self._data:
                    self._data[exec_id].update(fields)

        def append_log(self, exec_id, msg):
            with self._lock:
                if exec_id in self._data:
                    ts = time.strftime('%H:%M:%S')
                    self._data[exec_id]["logs"].append(f"{ts} {msg}")

        def get(self, exec_id):
            with self._lock:
                return self._data.get(exec_id)

    EXEC = ExecutionStore()

    _AUTO_LOCKS = {} 
    def _get_auto_lock(automation_id):
        _AUTO_LOCKS.setdefault(automation_id, threading.Lock())
        return _AUTO_LOCKS[automation_id]
    
    def _run_job(exec_id, automation_id, params, file_path_or_none, controller_callable):
        EXEC.set(exec_id, status="running", started_at=time.time())
        EXEC.append_log(exec_id, f"Automation: {automation_id}")
        try:

            with _get_auto_lock(automation_id):
                result = controller_callable(automation_id, params, file_path_or_none)

            EXEC.set(exec_id, status="done", finished_at=time.time(), output=result)
            EXEC.append_log(exec_id, "Finished with success.")
        except Exception as e:
            EXEC.set(exec_id, status="failed", finished_at=time.time(), error=str(e))
            EXEC.append_log(exec_id, f"ERROR: {e}")
        finally:
            if file_path_or_none and os.path.exists(file_path_or_none):
                try:
                    os.remove(file_path_or_none)
                except:
                    pass

    init_db(app)
    app.config.from_mapping(
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", ""),
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=int(os.getenv("JWT_EXPIRE_MIN", "30"))),
        
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ECHO=True,
        
        # Security
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key"),
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,
    )
    
    # Configuração de teste (se for o caso)
    if test_config is None:
        # Carregar config de produção do arquivo instance/config.py, se existir
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Carregar config de teste passada como parâmetro
        app.config.from_mapping(test_config)
    
    # Configurar CORS PRIMEIRO
    _configure_cors(app)
    
    # Inicializar extensões
    _initialize_extensions(app)
    
    # Configurar API
    api = _configure_api(app)
    
    # Registrar namespaces
    _register_namespaces(api)
    
    # Registrar rotas básicas
    _register_routes(app)
    
    # Registrar handlers de erro
    _register_error_handlers(app)
    
    return app

def _initialize_extensions(app):
    """Inicializar todas as extensões Flask"""
    # JWT
    jwt = JWTManager(app)
    
def _configure_api(app):
    authorizations = {
        "Bearer Auth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Use: Bearer <token>"
        }
    }
    
    return Api(app, 
               doc="/docs", 
               title="Automations API", 
               version="1.0", 
               authorizations=authorizations, 
               security="Bearer Auth")

def _register_namespaces(api):
    """Registrar todos os namespaces do Flask-RESTX"""
    api.add_namespace(auto_ns, path="/toFront")
    api.add_namespace(auth_ns, path="/auth")
    api.add_namespace(solicitacao_carga_ns, path="/solicitacao-carga")
    api.add_namespace(conciliacao_cdc_honda_ns, path="/conciliacao-cdc-honda")
    api.add_namespace(baixa_arquivos_cnh_honda_ns, path="/baixa-arquivos-cnh-honda")
    api.add_namespace(preparacao_baixas_ns, path="/preparacao-baixas")
    api.add_namespace(abrir_driver_ns, path="/abrir-driver")
    api.add_namespace(aymore_ns, path="/aymore")
    api.add_namespace(fidc_ns, path="/fidc")
    api.add_namespace(pan_ns, path="/pan")

def _configure_cors(app):
    CORS(
        app,
        resources={
            r"/automation/*": {
                "origins": [
                    "https://liliauto.flutterflow.app",
                    "http://127.0.0.1:5500",
                    "http://localhost:5500",
                    "http://localhost:8982",
                    r"http://localhost:\d+",
                ],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Authorization", "authorization", "Content-Type", "X-Requested-With"],
                "expose_headers": ["Authorization", "Content-Type"],
                "supports_credentials": False,
            }
        },
        supports_credentials=False,
    )

    @app.after_request
    def _add_cors_on_all(resp):
        origin = request.headers.get("Origin", "")
        if origin in ("http://127.0.0.1:5500", "http://localhost:5500"):
            resp.headers.setdefault("Access-Control-Allow-Origin", origin)
            resp.headers.setdefault("Vary", "Origin")
            resp.headers.setdefault("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Requested-With")
            resp.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
            resp.headers.setdefault("Access-Control-Expose-Headers", "Authorization, Content-Type")
        return resp

def _register_routes(app):
    """Registrar rotas básicas da aplicação"""
    
    @app.get("/health")
    def health():
        """Health check endpoint"""
        return {
            "status": "ok", 
            "service": "Automations API",
            "environment": os.getenv("FLASK_ENV", "development")
        }, 200

    @app.get("/", endpoint="index_redirect")
    def index_redirect():
        """Redirect para documentação da API"""
        return redirect("/docs", code=302)
    
    @app.get("/info")
    def app_info():
        """Informações da aplicação"""
        return {
            "app_name": "Automations API",
            "version": "1.0.0",
            "environment": os.getenv("FLASK_ENV", "development"),
            "debug_mode": app.debug
        }

def _register_error_handlers(app):
    """Registrar handlers para erros HTTP"""
    
    @app.errorhandler(404)
    def not_found(error):
        return {
            "error": "Endpoint não encontrado",
            "message": "A rota solicitada não existe",
            "path": request.path
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {
            "error": "Erro interno do servidor",
            "message": "Algo deu errado no servidor"
        }, 500
    
    @app.errorhandler(413)
    def too_large(error):
        return {
            "error": "Arquivo muito grande",
            "message": "O arquivo excede o tamanho máximo permitido de 50MB"
        }, 413
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {
            "error": "Não autorizado",
            "message": "Token de acesso inválido ou expirado"
        }, 401

# Ponto de entrada para desenvolvimento
if __name__ == "__main__":
    # Criar a aplicação usando a factory
    app = create_app()
    
    @app.get("/db/health")
    def db_health():
        try:
            with db.engine.connect() as conn:
                conn.execute(text("select 1"))
            return {"db": "ok"}, 200
        except Exception as e:
            # loga a causa e devolve 503 (serviço indisponível)
            app.logger.exception("DB healthcheck falhou: %s", e)
            return {"db": "down", "error": str(e)}, 503
    # Configurações de execução
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
     
    print(f"🚀 Iniciando Automations API...")
    print(f"📍 Host: {host}")
    print(f"🔧 Port: {port}")
    print(f"🐛 Debug: {debug}")
    print(f"📁 Instance Dir: {INSTANCE_DIR}")

    
    app.run(port=port, host=host, debug=debug, threaded=True)