from flask import jsonify, make_response
from flask_restx import Namespace
from APP.common.protected_resource import ProtectedResource
from APP.Services.abrir_driver_service import abrir_driver_main


abrir_driver_ns = Namespace('abrir-driver', description='Abre a instância do driver')

@abrir_driver_ns.route("/")
class ConciliacaoCDCHonda(ProtectedResource):
    def get(self):
        try:
            # chama seu orquestrador já com o parâmetro da rota
            abrir_driver_main()
            return jsonify({"ok": True, "resultado": 'Driver aberto com sucesso!'})
        except ValueError as ve:
            # erros de validação (lojas inexistentes, listas desbalanceadas etc.)
            return make_response(jsonify({"ok": False, "erro": str(ve)}), 400)
        except Exception as e:
            # erros inesperados
            return make_response(jsonify({"ok": False, "erro": str(e)}), 500)

