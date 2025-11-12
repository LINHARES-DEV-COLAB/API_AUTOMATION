from flask import Flask, request, jsonify, make_response
from flask_restx import Namespace, Resource
from APP.Services.solicitacao_carga_service import solicitacao_carga_main
from APP.Config.ihs_config import _ensure_driver
from APP.Config.ihs_config import request_stop, is_running
from datetime import datetime
from threading import Thread

solicitacao_carga_ns = Namespace('solicitacao-carga', description='Automação de Solicitação de Carga da CNH Honda')

@solicitacao_carga_ns.route("/<lojas>")
class SolicitacaoCarga(Resource):
    def get(self, lojas: str):
        hoje = datetime.now().strftime('%d-%m-%Y')
        session_id = f'Solicitação de Carga - {hoje}'

        if is_running(session_id):
            return make_response(jsonify({"ok": False, "erro": "already_running"}), 400)
        
        try:
            # chama seu orquestrador já com o parâmetro da rota
            t = Thread(target=solicitacao_carga_main, args=(session_id, lojas), daemon=True)
            t.start()
            return jsonify({"ok": True, "resultado": "✔ Solicitação de carga iniciada e executando em segundo plano.."})
        except ValueError as ve:

            return make_response(jsonify({"ok": False, "erro": str(ve)}), 400)
        except Exception as e:
            # erros inesperados
            return make_response(jsonify({"ok": False, "erro": str(e)}), 500)

@solicitacao_carga_ns.route("/stop")
class SolicitacaoCargaStop(Resource):
    def get(self):
        hoje = datetime.now().strftime('%d-%m-%Y')
        session_id = f'Solicitação de Carga - {hoje}'

        request_stop(session_id)
        return jsonify({"ok": True, "resultado": "stop_requested"})


@solicitacao_carga_ns.route("/go/<url>")
class Teste(Resource):
    def get(self, url: str):
        global _driver
        global _lock

        try:
            driver, wdw, PASTA_DOWNLOADS = _ensure_driver()
            _driver = driver
            driver.get(f'https://www.{url}.com')
            return jsonify({"ok": True, "resultado": 'Tudo certo'})
        except ValueError as ve:
            # erros de validação (lojas inexistentes, listas desbalanceadas etc.)
            return make_response(jsonify({"ok": False, "erro": str(ve)}), 400)
        except Exception as e:
            # erros inesperados
            return make_response(jsonify({"ok": False, "erro": str(e)}), 500)