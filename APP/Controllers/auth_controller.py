# APP/Controllers/auth_controller.py
from flask import Blueprint, request
from flask_restx import Api, Namespace, Resource, fields
from APP.Config.auth_ldap import autenticar_upn, buscar_atributos

auth_bp = Blueprint("auth", __name__)
api = Api(auth_bp)
auth_ns = Namespace("auth", description="Autenticação LDAP")
api.add_namespace(auth_ns)

login_model = auth_ns.model("Login", {
    "username": fields.String(required=True, description="Usuário"),
    "password": fields.String(required=True, description="Senha"),
})

@auth_ns.route("/health")
class Health(Resource):
    def get(self):
        return {"status": "ok"}, 200

@auth_ns.route("/login")
class Login(Resource):
    @auth_ns.expect(login_model, validate=True)
    def post(self):
        data = request.get_json(silent=True) or {}
        usuario = data.get("username") or data.get("usuario")
        senha = data.get("password") or data.get("senha")

        ok, err = autenticar_upn(usuario, senha)
        if not ok:
            return {"ok": False, "error": str(err)}, 401

        ok_attr, attrs, _ = buscar_atributos(usuario, senha)
        claims = {"cn": attrs.get("cn"), "mail": attrs.get("mail")} if ok_attr and attrs else {}

        return {
            "ok": True,
            "message": "Autenticado com sucesso",
            "user": usuario,
            "claims": claims
        }, 200
