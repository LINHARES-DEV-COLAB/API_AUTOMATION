from flask import Flask, request, jsonify, make_response
from flask_restx import Namespace, Resource
from APP.Services.solicitacao_carga_service import solicitacao_carga_main
import os

solicitacao_carga_ns = Namespace('solicitacao-carga', description='Automação de Solicitação de Carga da CNH Honda')

@solicitacao_carga_ns.route("/solicitacao-carga/<lojas>", methods=["GET"])
class SolicitacaoCarga(Resource):
    def get(lojas: str):
        try:
            # chama seu orquestrador já com o parâmetro da rota
            status, resultado = solicitacao_carga_main(lojas)
            return jsonify({"ok": status, "resultado": resultado})
        except ValueError as ve:
            # erros de validação (lojas inexistentes, listas desbalanceadas etc.)
            return make_response(jsonify({"ok": status, "erro": str(ve)}), 400)
        except Exception as e:
            # erros inesperados
            return make_response(jsonify({"ok": status, "erro": str(e)}), 500)