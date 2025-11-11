from flask import request, jsonify
from flask_restx import Namespace, Resource, reqparse
from werkzeug.datastructures import FileStorage
from APP.Services.fidc_service import FIDCAutomation
from APP.common.protected_resource import ProtectedResource
import logging
import traceback

# Configurar logger
logger = logging.getLogger(__name__)

# Parser simplificado - apenas arquivo e lojas
fidc_parser = reqparse.RequestParser()
fidc_parser.add_argument(
    'arquivo_excel',
    type=FileStorage,
    location='files',
    required=True,
    help='Arquivo Excel com dados FIDC (obrigatório)'
)
fidc_parser.add_argument(
    'lojas',
    type=str,
    location='form',
    required=False,
    help='Lista de lojas separadas por vírgula (opcional)'
)

fidc_ns = Namespace('fidc', description='Automação FIDC - Processamento de notas fiscais')

@fidc_ns.route("/processar")
class FIDCProcessar(ProtectedResource):
    @fidc_ns.expect(fidc_parser)
    def post(self):
        """
        Processa arquivo Excel para automação FIDC
        """
        try:
            # Parse dos argumentos
            args = fidc_parser.parse_args()
            arquivo_excel = args['arquivo_excel']
            lojas_param = args['lojas']
            
            logger.info("📥 Iniciando processamento FIDC")
            
            # Validar arquivo Excel
            if not arquivo_excel:
                return {
                    "ok": False,
                    "erro": "Nenhum arquivo Excel enviado"
                }, 400
            
            filename = arquivo_excel.filename.lower()
            if not (filename.endswith('.xlsx') or filename.endswith('.xls')):
                return {
                    "ok": False,
                    "erro": "Arquivo deve ser Excel (.xlsx ou .xls)"
                }, 400
             
            logger.info(f"📁 Arquivo recebido: {filename}")
            
            # Preparar parâmetros para a service
            parameters = {
                'arquivo_excel': arquivo_excel
            }
            
            # Adicionar lojas se especificadas
            if lojas_param:
                lojas_lista = [loja.strip() for loja in lojas_param.split(',')]
                parameters['lojas'] = lojas_lista
                logger.info(f"🏪 Lojas especificadas: {lojas_lista}")
            
            # Executar automação
            fidc_service = FIDCAutomation()
            
            # Validar parâmetros
            if not fidc_service.validate_parameters(parameters):
                return {
                    "ok": False,
                    "erro": "Parâmetro arquivo_excel é obrigatório"
                }, 400
            
            logger.info("🚀 Executando automação FIDC...")
            resultado = fidc_service.execute(parameters)
            
            # Formatar resposta de sucesso
            response_data = {
                "ok": True,
                "mensagem": "Automação FIDC executada com sucesso",
                "resultado": resultado,
                "detalhes": {
                    "arquivo_processado": filename,
                    "total_empresas": resultado.get('total_empresas', 0),
                    "empresas_com_sucesso": resultado.get('empresas_com_sucesso', 0),
                    "status_geral": resultado.get('status', 'unknown')
                }
            }
            
            logger.info("✅ Automação FIDC concluída com sucesso")
            return jsonify(response_data), 200
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento FIDC: {str(e)}")
            logger.error(traceback.format_exc())
            
            return {
                "ok": False,
                "erro": f"Falha na automação FIDC: {str(e)}"
            }, 500

@fidc_ns.route("/status")
class FIDCStatus(Resource):
    def get(self):
        """
        Retorna status do serviço FIDC
        """
        return {
            "ok": True,
            "servico": "FIDC Automation",
            "status": "operacional",
            "descricao": "Serviço de automação FIDC para processamento de notas fiscais"
        }, 200