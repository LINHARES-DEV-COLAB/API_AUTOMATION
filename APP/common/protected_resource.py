from flask_restx import Resource
from flask_jwt_extended import jwt_required

class ProtectedResource(Resource):
    """Base que protege todos os métodos da resource com JWT."""
    method_decorators = [jwt_required()]