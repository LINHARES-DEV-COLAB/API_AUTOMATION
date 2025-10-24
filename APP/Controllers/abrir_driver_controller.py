from flask import jsonify, make_response
from flask_restx import Namespace
from APP.common.protected_resource import ProtectedResource
from APP.Config.ihs_config import _ensure_driver


abrir_driver_ns = Namespace('abrir-driver', description='Abre a instância do driver')

@abrir_driver_ns.route("/")
class ConciliacaoCDCHonda(ProtectedResource):
    def get(self):
        try:
            # chama seu orquestrador já com o parâmetro da rota
            driver, wdw, PASTA_DOWNLOAD = _ensure_driver()
            return jsonify({"ok": True, "resultado": 'Driver aberto com sucesso!'})
        except ValueError as ve:
            # erros de validação (lojas inexistentes, listas desbalanceadas etc.)
            return make_response(jsonify({"ok": False, "erro": str(ve)}), 400)
        except Exception as e:
            # erros inesperados
            return make_response(jsonify({"ok": False, "erro": str(e)}), 500)

