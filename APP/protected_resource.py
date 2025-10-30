# APP/protected_resource.py
from functools import wraps
from flask_restx import Resource
from flask_jwt_extended import verify_jwt_in_request
from flask import jsonify

def _jwt_guard(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception as e:
            # RETORNE dict + code, NÃO jsonify()!
            return {"error": "Não autorizado", "message": str(e)}, 401
        return fn(*args, **kwargs)
    return wrapper

class ProtectedResource(Resource):
    """
    Base class para proteger endpoints do Flask-RESTX.
    Todas as methods (GET/POST/...) exigem JWT válido.
    """
    method_decorators = [_jwt_guard]
