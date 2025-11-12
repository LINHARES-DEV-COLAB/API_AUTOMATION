from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token
import sys
import os
from datetime import timedelta

# Configurar path - UMA VEZ só no topo
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Agora importe normalmente
from APP.Config.auth_ldap import autenticar_upn, buscar_atributos

auth_ns = Namespace("auth", description="Autenticação LDAP")

login_model = auth_ns.model("Login", {
    "username": fields.String(required=True, description="Usuário"),
    "password": fields.String(required=True, description="Senha"),
})

@auth_ns.route("/login")
class Login(Resource):
    @auth_ns.expect(login_model, validate=True)
    @auth_ns.doc(security=[])
    def post(self):
        data = request.get_json(silent=True) or {}
        usuario = data.get("username") or data.get("usuario")
        senha = data.get("password") or data.get("senha")

        # Nunca logar senha. Trate exceções.
        try:
            ok, err = autenticar_upn(usuario, senha)
        except Exception as e:
            auth_ns.logger.exception("Falha no backend de auth")
            return {"ok": False, "error": "internal_error"}, 500

        if not ok:
            return {"ok": False, "error": str(err) if err else "unauthorized"}, 401

        ok_attr, attrs, _ = buscar_atributos(usuario, senha)
        print(attrs)
        print(ok_attr)
        claims = {"cn": attrs.get("cn"), "mail": attrs.get("mail"),"department": attrs.get("department"),"description": attrs.get("description"),"samaccountname":attrs.get("samaccountname") } if ok_attr and attrs else {}

        identity =  usuario 

        access_token = create_access_token(identity=identity, additional_claims=claims, expires_delta=timedelta(hours=10))

        return {
            "ok": True,
            "message": "Autenticado com sucesso",
            "user": access_token,
            "claims": claims,
            "username":identity
        }, 200