from flask import Flask
from flask_cors import CORS
import os
from .Config.settings import config

def create_app(test_config=None):
    """
    Factory function para criar e configurar a aplicação Flask
    """
    # Criar instância do Flask
    app = Flask(__name__, instance_relative_config=True)
    
    # Configurações básicas
    app.config.from_mapping(
        SECRET_KEY=config.SECRET_KEY,
        MAX_CONTENT_LENGTH=config.MAX_CONTENT_LENGTH,
        JSONIFY_PRETTYPRINT_REGULAR=True
    )
    
    # Configuração de teste (se for o caso)
    if test_config is None:
        # Carregar config de produção, se existir
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Carregar config de teste
        app.config.from_mapping(test_config)
    
    # Garantir que as pastas existam
    try:
        config.create_directories()
    except OSError:
        pass
    
    # Configurar CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Registrar Blueprints/Controllers
    _register_blueprints(app)
    
    # Registrar rotas básicas
    _register_routes(app)
    
    # Registrar handlers de erro
    _register_error_handlers(app)
    
    return app

def _register_blueprints(app):
    """Registrar todos os blueprints/controllers"""
    from pan_controller import bp as pan_bp
    app.register_blueprint(pan_bp)
    
    # Futuros blueprints podem ser adicionados aqui
    # from .Controllers.user_controller import bp as user_bp
    # app.register_blueprint(user_bp)

def _register_routes(app):
    """Registrar rotas básicas da aplicação"""
    
    @app.route('/')
    def home():
        return {
            'message': 'Baixa Bancária PAN API - Flask',
            'status': 'online',
            'version': '1.0.0'
        }
    
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy',
            'timestamp': '2024-01-01T00:00:00Z'  # Usar datetime em produção
        }
    
    @app.route('/info')
    def app_info():
        return {
            'app_name': 'Baixa Bancária PAN',
            'environment': os.getenv('FLASK_ENV', 'development'),
            'debug_mode': app.debug
        }

def _register_error_handlers(app):
    """Registrar handlers para erros HTTP"""
    
    @app.errorhandler(404)
    def not_found(error):
        return {
            'error': 'Endpoint não encontrado',
            'message': str(error)
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {
            'error': 'Erro interno do servidor',
            'message': 'Algo deu errado no servidor'
        }, 500
    
    @app.errorhandler(413)
    def too_large(error):
        return {
            'error': 'Arquivo muito grande',
            'message': 'O arquivo excede o tamanho máximo permitido'
        }, 413