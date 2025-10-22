from flask import Flask, request, jsonify, make_response
from flask_restx import Namespace, Resource
from APP.Services.conciliacao_cdc_honda_service import conciliacao_cdc_honda_main

conciliacao_cdc_honda_ns = Namespace('conciliacao-cdc-honda', description='Automação de Solicitação de Carga da CNH Honda')

@conciliacao_cdc_honda_ns.route("/<lojas>", methods=["POST"])
class ConciliacaoCDCHonda(Resource):
    def post(self, lojas: str):
        try:
            # chama seu orquestrador já com o parâmetro da rota
            status, resultado = conciliacao_cdc_honda_main(lojas)
            return jsonify({"ok": status, "resultado": resultado})
        except ValueError as ve:
            # erros de validação (lojas inexistentes, listas desbalanceadas etc.)
            return make_response(jsonify({"ok": status, "erro": str(ve)}), 400)
        except Exception as e:
            # erros inesperados
            return make_response(jsonify({"ok": status, "erro": str(e)}), 500)

