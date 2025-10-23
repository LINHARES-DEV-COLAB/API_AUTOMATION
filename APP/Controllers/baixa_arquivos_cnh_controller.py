from flask import Flask, request, jsonify, make_response
from flask_restx import Namespace, Resource
from APP.Services.baixa_arquivos_cnh_honda_service import baixa_arquivos_cnh_honda_main
from APP.common.protected_resource import ProtectedResource

baixa_arquivos_cnh_honda_ns = Namespace('baixa-arquivos-cnh-honda', description='Automação de Baixa de arquivos da CNH Honda')

@baixa_arquivos_cnh_honda_ns.route("/<lojas>", methods=["POST"])
class ConciliacaoCDCHonda(ProtectedResource):
    def post(self, lojas: str):
        try:
            # chama seu orquestrador já com o parâmetro da rota
            status, resultado = baixa_arquivos_cnh_honda_main(lojas)
            return jsonify({"ok": status, "resultado": resultado})
        except ValueError as ve:
            # erros de validação (lojas inexistentes, listas desbalanceadas etc.)
            return make_response(jsonify({"ok": status, "erro": str(ve)}), 400)
        except Exception as e:
            # erros inesperados
            return make_response(jsonify({"ok": status, "erro": str(e)}), 500)

