# main.py - VERSÃO CORRIGIDA
from datetime import timedelta
import os
from pathlib import Path
from flask import Flask, redirect, jsonify, request 
from flask_cors import CORS
from flask_restx import Api
from flask_jwt_extended import JWTManager
from APP.Services import pan_service
from APP.extensions_service import db
from APP.Controllers.auth_controller import auth_ns
from APP.Controllers.solicitacao_carga_controller import solicitacao_carga_ns
from APP.Controllers.conciliacao_cdc_honda_controller import conciliacao_cdc_honda_ns
from APP.Controllers.baixa_arquivos_cnh_controller import baixa_arquivos_cnh_honda_ns
from APP.Controllers.preparacao_baixas_controller import preparacao_baixas_ns
from APP.Controllers.pan_controller import baixas_pan_ns

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = Path(os.getenv("INSTANCE_DIR", BASE_DIR / "instance")).resolve()
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = INSTANCE_DIR / "catalog.db"

def create_app(test_config=None):
    """
    Factory function para criar e configurar a aplicação Flask
    """
    # Criar instância do Flask
    app = Flask(__name__, 
                instance_relative_config=True, 
                instance_path=str(INSTANCE_DIR))

    # Configurações básicas
    app.config.from_mapping(
        # JWT Config
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", ""),
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=int(os.getenv("JWT_EXPIRE_MIN", "30"))),
        
        # Database Config
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{DB_PATH}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ECHO=True,
        
        # Security
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key"),
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50MB
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
    
    # Database
    db.init_app(app)
    
    # Criar tabelas (se necessário)
    with app.app_context():
        db.create_all()

def _configure_api(app):
    """Configurar Flask-RESTX API"""
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
    api.add_namespace(auth_ns, path="/auth")
    api.add_namespace(solicitacao_carga_ns, path="/solicitacao-carga")
    api.add_namespace(baixas_pan_ns, path="/baixas-pan")
    api.add_namespace(conciliacao_cdc_honda_ns, path="/conciliacao-cdc-honda")
    api.add_namespace(baixa_arquivos_cnh_honda_ns, path="/baixa-arquivos-cnh-honda")
    api.add_namespace(preparacao_baixas_ns, path="/preparacao-baixas")

def _configure_cors(app):
    """Configurar CORS"""
    CORS(
        app,
        resources={
            r"/*": {
                "origins": ["http://127.0.0.1:5500", "http://localhost:5500"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
                "supports_credentials": True
            }
        }
    )

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
            "debug_mode": app.debug,
            "database": str(DB_PATH)
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
    
    # Configurações de execução
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    print(f"🚀 Iniciando Automations API...")
    print(f"📍 Host: {host}")
    print(f"🔧 Port: {port}")
    print(f"🐛 Debug: {debug}")
    print(f"📁 Instance Dir: {INSTANCE_DIR}")
    print(f"🗄️  Database: {DB_PATH}")
    
    app.run(port=port, host=host, debug=debug)