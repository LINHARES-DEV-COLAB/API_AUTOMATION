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

# Parser para base64 (removido lojas)
fidc_parser = reqparse.RequestParser()
fidc_parser.add_argument(
    'arquivo_base64',
    type=str,
    location='json',
    required=True,
    help='Arquivo Excel em base64 (obrigatório)'
)

fidc_ns = Namespace('fidc', description='Automação FIDC - Processamento de notas fiscais')

def executar_fidc_em_background(session_id, parameters):
    """
    Executa o FIDC em background
    """
    try:
        logger.info("🚀 Iniciando processamento FIDC em background...")
        fidc_service = FIDCAutomation()
        resultado = fidc_service.execute(parameters)
        
        # Limpar arquivo temporário
        if 'arquivo_excel' in parameters and os.path.exists(parameters['arquivo_excel']):
            os.unlink(parameters['arquivo_excel'])
            logger.info("🧹 Arquivo temporário removido")
            
        logger.info("✅ Processamento FIDC em background concluído")
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Erro no processamento FIDC em background: {str(e)}")
        # Limpar arquivo temporário em caso de erro
        try:
            if 'arquivo_excel' in parameters and os.path.exists(parameters['arquivo_excel']):
                os.unlink(parameters['arquivo_excel'])
        except:
            pass
        return {
            "status": "error",
            "erro": str(e)
        }

@fidc_ns.route("/processar")
class FIDCProcessar(ProtectedResource):
    @fidc_ns.expect(fidc_parser)
    def post(self):
        temp_file_path = None
        session_id = 'FIDC - envio de boletos'
        
        if is_running(session_id):
            return make_response(jsonify({"ok":False, "erro":"already_running"}), 400)

        try:
            args = fidc_parser.parse_args()
            arquivo_base64 = args['arquivo_base64']
            
            logger.info("📥 Iniciando processamento FIDC com base64 - TODAS AS EMPRESAS")

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
            
            # Preparar parâmetros para a service (SEM lojas - processa todas automaticamente)
            parameters = {
                'arquivo_excel': temp_file_path
            }
            
            logger.info("🏪 Processando TODAS as empresas encontradas no arquivo Excel")
            
            # Iniciar processamento em background
            thread = Thread(
                target=executar_fidc_em_background,
                args=(session_id, parameters),
                daemon=True
            )
            thread.start()
            
            # Retornar resposta imediata
            response_data = {
                "ok": True,
                "mensagem": "Processamento FIDC iniciado em background - TODAS as empresas serão processadas",
                "session_id": session_id,
                "detalhes": {
                    "modo": "processamento_automatico",
                    "empresas": "todas_as_encontradas_no_excel",
                    "status": "iniciado"
                }
            }
            
            logger.info("🚀 Processamento FIDC iniciado em background para TODAS as empresas")
            return jsonify(response_data), 202  # 202 Accepted para processos assíncronos
            
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
