from flask import make_response, request, jsonify
from flask_restx import Namespace, Resource, reqparse
from APP.Services.fidc_service import FIDCAutomation
from APP.common.protected_resource import ProtectedResource
from APP.Config.ihs_config import is_running
import logging
import traceback
import base64
import tempfile
import os
from threading import Thread

# Configurar logger
logger = logging.getLogger(__name__)

# Parser para base64 e lojas opcional
fidc_parser = reqparse.RequestParser()
fidc_parser.add_argument(
    'arquivo_base64',
    type=str,
    location='json',
    required=True,
    help='Arquivo Excel em base64 (obrigatório)'
)
fidc_parser.add_argument(
    'lojas',
    type=str,
    location='json',
    required=False,
    help='Lista de lojas separadas por vírgula (opcional)'
)
fidc_parser.add_argument(
    'nome_arquivo',
    type=str,
    location='json',
    required=False,
    help='Nome do arquivo original (opcional)'
)

fidc_ns = Namespace('fidc', description='Automação FIDC - Processamento de notas fiscais')

@fidc_ns.route("/processar")
class FIDCProcessar(ProtectedResource):
    @fidc_ns.expect(fidc_parser)
    def post(self):

        temp_file_path = None
        session_id = f'FIDC - envio de boletos'
        if is_running(session_id):
            return make_response(jsonify({"ok":False, "erro":"already_running"}), 400)

        try:
            args = fidc_parser.parse_args()
            arquivo_base64 = args['arquivo_base64']
            lojas_param = args['lojas']
            nome_arquivo = args.get('nome_arquivo', 'arquivo.xlsx')
            
            logger.info("📥 Iniciando processamento FIDC com base64")
            
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
            if lojas_param:
                logger.info(f"🏪 Lojas especificadas: {lojas_param}")
            
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
            
            # Adicionar lojas se especificadas
            if lojas_param:
                lojas_lista = [loja.strip() for loja in lojas_param.split(',')]
                parameters['lojas'] = lojas_lista
                logger.info(f"🏪 Lojas processadas: {lojas_lista}")
            
            
            fidc_service = Thread(targed=FIDCAutomation(), args=(session_id, lojas_lista), daemon=True)
            
            # Validar parâmetros
            if not fidc_service.validate_parameters(parameters):
                # Limpar arquivo temporário
                if temp_file_path and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                
                return {
                    "ok": False,
                    "erro": "Parâmetro arquivo_excel é obrigatório"
                }, 400
            
            logger.info("🚀 Executando automação FIDC...")
            resultado = fidc_service.execute(parameters)
            
            # Limpar arquivo temporário
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.info("🧹 Arquivo temporário removido")
            
            # Formatar resposta de sucesso
            response_data = {
                "ok": True,
                "mensagem": "Automação FIDC executada com sucesso",
                "resultado": resultado,
                "detalhes": {
                    "arquivo_processado": nome_arquivo,
                    "total_empresas": resultado.get('total_empresas', 0),
                    "empresas_com_sucesso": resultado.get('empresas_com_sucesso', 0),
                    "status_geral": resultado.get('status', 'unknown'),
                    "total_nfs_excel": resultado.get('total_nfs_excel', 0),
                    "total_nfs_processadas": resultado.get('total_nfs_processadas', 0),
                    "total_boletos_gerados": resultado.get('total_boletos_gerados', 0),
                    "eficiencia_geral": resultado.get('eficiencia_geral', 0)
                }
            }
            
            logger.info("✅ Automação FIDC concluída com sucesso")
            return jsonify(response_data), 200
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento FIDC: {str(e)}")
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