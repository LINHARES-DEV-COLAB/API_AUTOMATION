from flask import Flask, request, jsonify, make_response
from flask_restx import Namespace, Resource
from APP.Services.conciliacao_cdc_honda_service import conciliacao_cdc_honda_main
from APP.common.protected_resource import ProtectedResource
from threading import Thread
from APP.Config.ihs_config import request_stop, is_running
from datetime import datetime


conciliacao_cdc_honda_ns = Namespace('conciliacao-cdc-honda', description='Automação de conciliação de dados bancários de Financiamento Honda')

@conciliacao_cdc_honda_ns.route("/<lojas>")
class ConciliacaoCDCHonda(ProtectedResource):
    def post(self, lojas: list):
        hoje = datetime.now().strftime('%d-%m-%Y')
        session_id = f'Conciliação CDC Honda - {hoje}'

        if is_running(session_id):
            return make_response(jsonify({"ok": False, "erro": "already_running"}), 400)

        try:
            # chama seu orquestrador já com o parâmetro da rota
            t = Thread(target=conciliacao_cdc_honda_main, args=(session_id, lojas), daemon=True)
            t.start()
            return jsonify({"ok": True, "resultado": "✔ Conciliação dos valores iniciada e executando em segundo plano.."})
        except ValueError as ve:
            # erros de validação (lojas inexistentes, listas desbalanceadas etc.)
            return make_response(jsonify({"ok": False, "erro": str(ve)}), 400)
        except Exception as e:
            # erros inesperados
            return make_response(jsonify({"ok": False, "erro": str(e)}), 500)

@conciliacao_cdc_honda_ns.route("/stop")
class ConciliacaoCDCHondaStop(ProtectedResource):
    def post(self):
        hoje = datetime.now().strftime('%d-%m-%Y')
        session_id = f'Conciliação CDC Honda - {hoje}'

        request_stop(session_id)
        return jsonify({"ok": True, "resultado": "stop_requested"})

