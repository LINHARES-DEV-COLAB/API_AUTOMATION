from flask import request, jsonify
from flask_restx import Namespace, Resource, reqparse
from werkzeug.datastructures import FileStorage
from APP.Services.pan_service import PanService
from APP.common.protected_resource import ProtectedResource
import logging
import traceback

# Configurar logger
logger = logging.getLogger(__name__)

# Parser para upload de arquivo e data opcional
pan_parser = reqparse.RequestParser()
pan_parser.add_argument(
    'arquivo_excel',
    type=FileStorage,
    location='files',
    required=True,
    help='Arquivo Excel com extrato Itaú (obrigatório)'
)
pan_parser.add_argument(
    'data',
    type=str,
    location='form',
    required=False,
    help='Data específica para busca no formato DD-MM-AAAA (opcional)'
)

pan_ns = Namespace('pan', description='Automação PAN - Processamento de extratos bancários')

@pan_ns.route("/processar")
class PANProcessar(ProtectedResource):
    @pan_ns.expect(pan_parser)
    def post(self):
        """
        Processa arquivo Excel para automação PAN
        """
        try:
            # Parse dos argumentos
            args = pan_parser.parse_args()
            arquivo_excel = args['arquivo_excel']
            data_param = args['data']
            
            logger.info("📥 Iniciando processamento PAN")
            
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
            if data_param:
                logger.info(f"📅 Data especificada: {data_param}")
            
            # Salvar arquivo temporariamente
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                arquivo_excel.save(tmp_file.name)
                temp_file_path = tmp_file.name
            
            # Preparar parâmetros para a service
            parameters = {
                'arquivo_excel': temp_file_path
            }
            
            # Adicionar data se especificada
            if data_param:
                parameters['data'] = data_param
            
            # Executar automação
            pan_service = PanService()
            
            logger.info("🚀 Executando automação PAN...")
            resultado = pan_service.processar_extrato(parameters)
            
            # Limpar arquivo temporário
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            # Verificar se houve erro na execução
            if resultado.get('status') == 'error':
                return {
                    "ok": False,
                    "erro": f"Falha na automação PAN: {resultado.get('erro', 'Erro desconhecido')}"
                }, 500
            
            # Formatar resposta de sucesso
            response_data = {
                "ok": True,
                "mensagem": resultado.get('mensagem', 'Automação PAN executada com sucesso'),
                "resultado": resultado,
                "detalhes": {
                    "arquivo_processado": filename,
                    "total_processado": resultado.get('total_processado', 0),
                    "resultados_encontrados": len(resultado.get('resultados', [])),
                    "status": resultado.get('status', 'completed')
                }
            }
            
            logger.info(f"✅ Automação PAN concluída: {resultado.get('total_processado', 0)} registros processados")
            return jsonify(response_data), 200
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento PAN: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Limpar arquivo temporário em caso de erro
            try:
                if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            except:
                pass
            
            return {
                "ok": False,
                "erro": f"Falha na automação PAN: {str(e)}"
            }, 500

@pan_ns.route("/status")
class PANStatus(Resource):
    def get(self):
        """
        Retorna status do serviço PAN
        """
        return {
            "ok": True,
            "servico": "PAN Automation",
            "status": "operacional",
            "descricao": "Serviço de automação PAN para processamento de extratos bancários"
        }, 200