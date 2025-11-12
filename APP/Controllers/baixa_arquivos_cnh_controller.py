from flask import Flask, request, jsonify, make_response
from flask_restx import Namespace, Resource
from APP.Services.baixa_arquivos_cnh_honda_service import baixa_arquivos_cnh_honda_main
from APP.common.protected_resource import ProtectedResource
from threading import Thread
from APP.Config.ihs_config import request_stop, is_running
from datetime import datetime


baixa_arquivos_cnh_honda_ns = Namespace('baixa-arquivos-cnh-honda', description='Automação de Baixa de arquivos da CNH Honda')

@baixa_arquivos_cnh_honda_ns.route("/<lojas>")
class BaixasCNHHonda(ProtectedResource):
    def post(self, lojas: str):
        hoje = datetime.now().strftime('%d-%m-%Y')
        session_id = f'Baixa de Arquivos de CNH Honda - {hoje}'

        if is_running(session_id):
            return make_response(jsonify({"ok": False, "erro": "already_running"}), 400)
        
        try:
            # chama seu orquestrador já com o parâmetro da rota
            t = Thread(target=baixa_arquivos_cnh_honda_main, args=(session_id, lojas), kwargs={"max_retries": 5}, daemon=True)
            t.start()
            return jsonify({"ok": True, "resultado": "✔ Baixas dos arquivos iniciada e executando em segundo plano.."})
        except ValueError as ve:
            # erros de validação (lojas inexistentes, listas desbalanceadas etc.)
            return make_response(jsonify({"ok": False, "erro": str(ve)}), 400)
        except Exception as e:
            # erros inesperados
            return make_response(jsonify({"ok": False, "erro": str(e)}), 500)

@baixa_arquivos_cnh_honda_ns.route("/stop")
class BaixasCNHHondaStop(ProtectedResource):
    def post(self,):
        hoje = datetime.now().strftime('%d-%m-%Y')
        session_id = f'Baixa de Arquivos de CNH Honda - {hoje}'

        request_stop(session_id)
        return jsonify({"ok": True, "resultado": "stop_requested"})

