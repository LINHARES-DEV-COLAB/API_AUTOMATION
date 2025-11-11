from flask import request, jsonify
from flask_restx import Namespace, Resource, reqparse
from APP.Services.pan_service import PanAutomation
from APP.common.protected_resource import ProtectedResource
import logging
import traceback
import base64
import tempfile
import os

# Configurar logger
logger = logging.getLogger(__name__)

# Parser para base64 e data opcional
pan_parser = reqparse.RequestParser()
pan_parser.add_argument(
    'arquivo_base64',
    type=str,
    location='json',
    required=True,
    help='Arquivo Excel em base64 (obrigatório)'
)
pan_parser.add_argument(
    'data',
    type=str,
    location='json',
    required=False,
    help='Data específica para busca no formato DD-MM-AAAA (opcional)'
)
pan_parser.add_argument(
    'nome_arquivo',
    type=str,
    location='json',
    required=False,
    help='Nome do arquivo original (opcional)'
)

pan_ns = Namespace('pan', description='Automação PAN - Processamento de extratos bancários')

@pan_ns.route("/processar")
class PANProcessar(ProtectedResource):
    @pan_ns.expect(pan_parser)
    def post(self):
        """
        Processa arquivo Excel em base64 para automação PAN
        """
        temp_file_path = None
        
        try:
            # Parse dos argumentos
            args = pan_parser.parse_args()
            arquivo_base64 = args['arquivo_base64']
            data_param = args['data']
            nome_arquivo = args.get('nome_arquivo', 'arquivo.xlsx')
            
            logger.info("📥 Iniciando processamento PAN com base64")
            
            # Validar base64
            if not arquivo_base64:
                return {
                    "ok": False,
                    "erro": "Nenhum arquivo base64 enviado"
                }, 400
            
            # Verificar se é um base64 válido (contém apenas caracteres base64 ou data URL)
            base64_data = arquivo_base64
            
            # Se for data URL, extrair apenas o base64
            if base64_data.startswith('data:'):
                logger.info("🔧 Detectado data URL, extraindo base64...")
                # Extrai o base64 puro do data URL
                base64_parts = base64_data.split(',')
                if len(base64_parts) == 2:
                    base64_data = base64_parts[1]
                else:
                    return {
                        "ok": False,
                        "erro": "Formato data URL inválido"
                    }, 400
            
            logger.info(f"📁 Processando arquivo: {nome_arquivo}")
            if data_param:
                logger.info(f"📅 Data especificada: {data_param}")
            
            # Decodificar base64 e salvar como arquivo temporário
            try:
                # Decodificar base64
                file_data = base64.b64decode(base64_data)
                
                # Criar arquivo temporário
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    tmp_file.write(file_data)
                    temp_file_path = tmp_file.name
                
                logger.info(f"✅ Arquivo temporário criado: {temp_file_path}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao decodificar base64: {str(e)}")
                return {
                    "ok": False,
                    "erro": f"Base64 inválido: {str(e)}"
                }, 400
            
            # Preparar parâmetros para a service
            parameters = {
                'arquivo_excel': temp_file_path
            }
            
            # Adicionar data se especificada
            if data_param:
                parameters['data'] = data_param
            
            # Executar automação
            pan_service = PanAutomation()
            
            # Validar parâmetros
            if not pan_service.validate_parameters(parameters):
                # Limpar arquivo temporário
                if temp_file_path and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                
                return {
                    "ok": False,
                    "erro": "Parâmetro arquivo_excel é obrigatório"
                }, 400
            
            logger.info("🚀 Executando automação PAN...")
            resultado = pan_service.execute(parameters)
            
            # Limpar arquivo temporário
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.info("🧹 Arquivo temporário removido")
            
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
                    "arquivo_processado": nome_arquivo,
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
                if temp_file_path and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    logger.info("🧹 Arquivo temporário removido após erro")
            except Exception as cleanup_error:
                logger.error(f"❌ Erro ao limpar arquivo temporário: {cleanup_error}")
            
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