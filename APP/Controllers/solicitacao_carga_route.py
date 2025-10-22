from flask import Flask, request, jsonify, make_response
from flask_restx import Namespace, Resource
from APP.Services.solicitacao_carga_service import solicitacao_carga_main
import os

solicitacao_carga_ns = Namespace('solicitacao-carga', description='Automação de Solicitação de Carga da CNH Honda')

@solicitacao_carga_ns.route('/solicitacao-carga')
class SolicitaCarga(Resource):
    def get(self):
        payload = request.get_json(silent=True) or {}
        all_flag = bool(payload.get("all"))
        lojas_list = payload.get("lojas")

        # Decisão da fonte (all vs lista)
        if all_flag:
            lojas_arg = "all"
        elif isinstance(lojas_list, list) and lojas_list:  # ex.: ["Ares Motos", "Cajazeiras"]
            lojas_arg = lojas_list
        else:
            return make_response(jsonify({
                "ok": False,
                "erro": "Informe {'all': true} ou {'lojas': ['...','...']}."
            }), 400)

        try:
            status, log = solicitacao_carga_main(lojas_arg)
            return jsonify({"ok": status, "resultado": log})
        except ValueError as ve:
            return make_response(jsonify({"ok": status, "erro": str(ve)}), 400)
        except Exception as e:
            return make_response(jsonify({"ok": status, "erro": str(e)}), 500)