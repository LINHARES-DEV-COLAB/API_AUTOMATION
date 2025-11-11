from shutil import ExecError
from flask_restx import Namespace, Resource
from APP.Services.aymore_service import AymoreService

aymore_ns = Namespace("aymore", description="Serviços relacionados ao Aymore")

@aymore_ns.route("/processar-dados")
class Aymore(Resource):
    def post(self):
        try:
            path = r"C:\Users\sousa.lima\Downloads\JUA SANT 04.xls"
            resultado = AymoreService().processar_aymore(path)
            return{
                "mensagem": "Dados processados com sucesso",
                "caminho_arquivo": path,
                "resultado": resultado
            }, 200
        
        except Exception as e:
            return {
                "erro": "Falha ao processar dados",
                "detalhes": str(e)
            }, 500
        