from flask import make_response, request, jsonify
from flask_restx import Namespace, Resource, reqparse
from werkzeug.datastructures import FileStorage
from APP.Services.pan_service import PanService
from APP.common.protected_resource import ProtectedResource
from APP.Config.ihs_config import is_running
import logging
import traceback
from threading import Thread
import os
import tempfile

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

def executar_processamento_pan(session_id, parameters):
    """
    Função para executar o processamento PAN em background
    """
    try:
        service = PanService()
        
        # Extrair parâmetros
        arquivo_excel = parameters['arquivo_excel']
        data_param = parameters.get('data')
        
        # Processar com ou sem data
        if data_param:
            resultados = service.processar_extrato_com_data(arquivo_excel, data_param)
        else:
            resultados = service.processar_extrato(arquivo_excel)
        
        # Converter resultados para dicionário
        resultados_dict = [resultado.to_dict() for resultado in resultados]
        
        return {
            "status": "completed",
            "mensagem": f"Processamento concluído - {len(resultados)} registros encontrados",
            "total_processado": len(resultados),
            "resultados": resultados_dict
        }
        
    except Exception as e:
        logger.error(f"Erro no processamento PAN em background: {str(e)}")
        return {
            "status": "error",
            "erro": str(e)
        }
    finally:
        # Limpar arquivo temporário
        if 'arquivo_excel' in parameters and os.path.exists(parameters['arquivo_excel']):
            try:
                os.unlink(parameters['arquivo_excel'])
            except Exception as e:
                logger.error(f"Erro ao limpar arquivo temporário: {e}")

@pan_ns.route("/processar")
class PANProcessar(ProtectedResource):
    @pan_ns.expect(pan_parser)
    def post(self):
        """
        Processa arquivo Excel para automação PAN
        """
        session_id = "FIDC - envio de boletos"
        if is_running(session_id):
            return make_response(jsonify({"ok":False,"erro":"already_running"}), 400)
        
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
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                arquivo_excel.save(tmp_file.name)
                temp_file_path = tmp_file.name
            
            # Preparar parâmetros para a thread
            parameters = {
                'arquivo_excel': temp_file_path
            }
            
            # Adicionar data se especificada
            if data_param:
                parameters['data'] = data_param
            
            # Iniciar thread em background
            t = Thread(
                target=executar_processamento_pan, 
                args=(session_id, parameters),
                daemon=True
            )
            t.start()
            
            logger.info("🚀 Processamento PAN iniciado em background")
            
            # Retornar resposta imediata
            response_data = {
                "ok": True,
                "mensagem": "Processamento PAN iniciado em background",
                "session_id": session_id,
                "detalhes": {
                    "arquivo_processado": filename,
                    "data_processamento": data_param if data_param else "automática",
                    "status": "iniciado"
                }
            }
            
            return jsonify(response_data), 202  # 202 Accepted para processos assíncronos
            
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