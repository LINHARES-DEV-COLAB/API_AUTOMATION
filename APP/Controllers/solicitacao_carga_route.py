from flask import Flask, request, jsonify, make_response
from flask_restx import Namespace, Resource
from APP.Services.solicitacao_carga_service import solicitacao_carga_main
from APP.Config.ihs_config import _ensure_driver
import threading
import os

_driver = None
_lock = threading.Lock()

solicitacao_carga_ns = Namespace('solicitacao-carga', description='Automação de Solicitação de Carga da CNH Honda')

@solicitacao_carga_ns.route("/<lojas>", methods=["POST"])
class SolicitacaoCarga(Resource):
    def post(self, lojas: str):
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



@solicitacao_carga_ns.route("/go/<url>", methods=["POST"])
class Teste(Resource):
    def post(self, url: str):
        global _driver
        global _lock

        try:
            driver, wdw, PASTA_DOWNLOADS = _ensure_driver(_driver, _lock)
            _driver = driver
            driver.get(f'https://www.{url}.com')
            return jsonify({"ok": True, "resultado": 'Tudo certo'})
        except ValueError as ve:
            # erros de validação (lojas inexistentes, listas desbalanceadas etc.)
            return make_response(jsonify({"ok": False, "erro": str(ve)}), 400)
        except Exception as e:
            # erros inesperados
            return make_response(jsonify({"ok": False, "erro": str(e)}), 500)