from flask import jsonify, make_response
from flask_restx import Namespace
from APP.Services.preparacao_baixas_service import extract_text_pdfplumber, verifica_dados_linx
from APP.common.protected_resource import ProtectedResource

preparacao_baixas_ns = Namespace('preparacao-baixas', description='Automação de Preparação de Baixas de CNH faltantes')

@preparacao_baixas_ns.route("/verifica_dados_linx/<nome_loja>")  # Lembrar de trocar o \ por /
class VerificacaoDadosLinx(ProtectedResource):
    def post(self, nome_loja: str):
        try:
            # chama seu orquestrador já com o parâmetro da rota
            status, resultado = verifica_dados_linx(nome_loja, path=r'\\172.17.67.14\findev$\Automação - CNH\Baixa de Arquivos\Arquivos Baixados')
            return jsonify({"ok": status, "resultado": resultado})
        except ValueError as ve:
            # erros de validação (lojas inexistentes, listas desbalanceadas etc.)
            return make_response(jsonify({"ok": False, "erro": str(ve)}), 400)
        except Exception as e:
            # erros inesperados
            return make_response(jsonify({"ok": False, "erro": str(e)}), 500)

@preparacao_baixas_ns.route("/extrair-pdf/<nome_loja>")  # Lembrar de trocar o \ por /
class ExtracaoPdf(ProtectedResource):
    def post(self, nome_loja: str):
        try:
            # chama seu orquestrador já com o parâmetro da rota
            status, resultado = extract_text_pdfplumber(nome_loja, path=r'\\172.17.67.14\findev$\Automação - CNH\Baixa de Arquivos\Arquivos Baixados')
            return jsonify({"ok": status, "resultado": resultado})
        except ValueError as ve:
            # erros de validação (lojas inexistentes, listas desbalanceadas etc.)
            return make_response(jsonify({"ok": False, "erro": str(ve)}), 400)
        except Exception as e:
            # erros inesperados
            return make_response(jsonify({"ok": False, "erro": str(e)}), 500)

