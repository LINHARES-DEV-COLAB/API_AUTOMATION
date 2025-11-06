from enum import auto
from http import HTTPStatus
from pdb import run
from click import Parameter
from flask import current_app, request
from flask_restx import Namespace, Resource, fields
from sqlalchemy.exc import SQLAlchemyError
from APP import Data
from APP.Config.supa_config import db
from APP.Models import executions_model
from APP.protected_resource import ProtectedResource
from APP.Models.sector_model import Sector
from APP.Models.automation_model import Automation
from APP.Models.run_model import Run  
from flask_restx import reqparse
from werkzeug.datastructures import FileStorage
from APP.Services.execution_service import ExecutionService
from APP.Models.executions_model import Execution  



auto_ns = Namespace("automation", description="Catálogo de setores, automações e execuções")

# ==== MODELS RESTX (apenas campos que você realmente expõe) ====
sector_model = auto_ns.model("Sector", {
    "id":   fields.String(required=True, description="ID do setor"),
    "name": fields.String(required=True, description="Nome do setor"),
})

automation_list_item = auto_ns.model("AutomationListItem", {
    "id": fields.String,
    "name": fields.String,
    "description": fields.String,
    "type": fields.String,
    "is_active": fields.Boolean,
    "department_id": fields.String,
    "created_by": fields.String,
    "updated_at": fields.String,
})

automation_list_response = auto_ns.model("AutomationListResponse", {
    "items": fields.List(fields.Nested(automation_list_item)),
    "page": fields.Integer,
    "pageSize": fields.Integer,
    "total": fields.Integer
})

run_model = auto_ns.model("Run", {
    "runId":        fields.Integer,
    "automationId": fields.String,
    "status":       fields.String,
    "startedAt":    fields.String,
    "finishedAt":   fields.String,
    "output":       fields.Raw,
})

executions_model = auto_ns.model("Execution", {
    "id": fields.Integer,
    "automation": fields.String,
    "department": fields.String,
    "status": fields.String
})

run_input_model = auto_ns.model("RunInput", {
    "lojas": fields.String(required=False),
    "url": fields.String(required=False),
    "param1": fields.String(required=False),
    "param2": fields.String(required=False),
    # Adicione outros parâmetros que suas automações podem usar
})

# NO automation_controller.py - ATUALIZE o upload_parser:

# NO automation_controller.py - ATUALIZE o upload_parser:

# upload_parser = reqparse.RequestParser()
# upload_parser.add_argument(
#     'arquivo_excel', 
#     type=FileStorage, 
#     location='files', 
#     required=False,  # ← Agora opcional
#     help='Arquivo Excel (opcional para algumas automações)'
# )
# upload_parser.add_argument(
#     'lojas', 
#     type=str, 
#     location='form', 
#     required=False,
#     action='split',
#     help='Lista de lojas para processar (opcional)'
# )
# upload_parser.add_argument(
#     'data', 
#     type=str, 
#     location='form', 
#     required=False,
#     help='Data específica para processamento (opcional)'
# )
# upload_parser.add_argument(
#     'url', 
#     type=str, 
#     location='form', 
#     required=False,
#     help='URL para acessar (opcional)'
# )
# upload_parser.add_argument(
#     'pasta_destino', 
#     type=str, 
#     location='form', 
#     required=False,
#     help='Pasta de destino para downloads (opcional)'
# )
# upload_parser.add_argument(
#     'data_inicio', 
#     type=str, 
#     location='form', 
#     required=False,
#     help='Data de início do período (opcional)'
# )
# upload_parser.add_argument(
#     'data_fim', 
#     type=str, 
#     location='form', 
#     required=False,
#     help='Data de fim do período (opcional)'
# )
# upload_parser.add_argument(
#     'filial', 
#     type=str, 
#     location='form', 
#     required=False,
#     help='Filial específica (opcional)'
# )
# upload_parser.add_argument(
#     'modo', 
#     type=str, 
#     location='form', 
#     required=False,
#     help='Modo de execução (opcional)'
# )
# # Adicione outros parâmetros conforme necessário

# NO automation_controller.py - SUBSTITUA o upload_parser por:

run_input_model = auto_ns.model("RunInput", {
    "arquivo_excel": fields.String(required=False, description="Base64 do arquivo Excel (opcional)"),
    "lojas": fields.List(fields.String, required=False, description="Lista de lojas para processar"),
    "data": fields.String(required=False, description="Data específica para processamento"),
    "url": fields.String(required=False, description="URL para acessar"),
    "pasta_destino": fields.String(required=False, description="Pasta de destino para downloads"),
    "data_inicio": fields.String(required=False, description="Data de início do período"),
    "data_fim": fields.String(required=False, description="Data de fim do período"),
    "filial": fields.String(required=False, description="Filial específica"),
    "modo": fields.String(required=False, description="Modo de execução"),
    # Adicione outros parâmetros conforme necessário
})

# ===== /automation/departments ===== (NÃO use jsonify aqui)
@auto_ns.route("/departments")
class Departments(ProtectedResource):  # use ProtectedResource se quiser JWT aqui
    @auto_ns.marshal_list_with(sector_model, code=HTTPStatus.OK, envelope=None)
    def get(self):
        try:
            # pegue somente as colunas necessárias e converta para dict simples
            rows = db.session.query(Sector.id, Sector.name).all()
            data = [{"id": str(i), "name": n} for (i, n) in rows]
            current_app.logger.info("[DEPARTMENTS] %d registros", len(data))
            return data, HTTPStatus.OK
        except Exception:
            current_app.logger.exception("[DEPARTMENTS] Erro")
            db.session.rollback()
            auto_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Internal Server Error")

# ===== /automation/automations/<department_id> =====
@auto_ns.route("/automations/<string:department_id>")
class Automations(ProtectedResource):  # use ProtectedResource se exigir JWT
    @auto_ns.marshal_with(automation_list_response, code=HTTPStatus.OK, envelope=None)
    def get(self, department_id: str):
        try:
            rows = (Automation.query
                    .filter(Automation.department_id == department_id)
                    .order_by(Automation.name)
                    .all())

            items = []
            for a in rows:
                if getattr(a, "is_active", False):
                    items.append({
                        "id": str(a.id),
                        "name": a.name,
                        "description": a.description,
                        "type": getattr(a, "type", None),
                        "is_active": bool(a.is_active),
                        "department_id": str(a.department_id) if getattr(a, "department_id", None) is not None else None,
                        "created_by": getattr(a, "created_by", None),
                        "updated_at": a.updated_at.isoformat() if getattr(a, "updated_at", None) else None,
                    })

            resp = {
                "items": items,
                "page": 1,
                "pageSize": len(items),
                "total": len(items)
            }
            return resp, HTTPStatus.OK

        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("[AUTOMATIONS] Erro de banco")
            auto_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Internal Server Error")
        except Exception:
            current_app.logger.exception("[AUTOMATIONS] Erro inesperado")
            auto_ns.abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Internal Server Error")


@auto_ns.route("/automations/<string:automation_id>/run")
class RunAutomation(ProtectedResource):
    @auto_ns.expect(run_input_model)  # Use o modelo JSON em vez do parser
    @auto_ns.marshal_with(run_model, code=HTTPStatus.ACCEPTED, envelope=None)
    def post(self, automation_id: str):
        execution_id = None
        temp_file_path = None

        try:
            parameters = {}
            
            # 1. BUSCAR AUTOMAÇÃO NO BANCO
            automation = Automation.query.get(automation_id)
            if not automation:
                return {"error": "Automação não encontrada"}, 404
            
            print(f"🔍 Automação: {automation_id}")
            print(f"📝 Script Path: {automation.script_path}")
            print(f"⚡ Tipo Execução: {automation.type}")
            
            # 2. PROCESSAR PARÂMETROS DO JSON BODY
            json_data = request.get_json() or {}
            print(f"📦 JSON recebido: {json_data}")
            
            # Processa arquivo em base64 (se fornecido)
            arquivo_excel_b64 = json_data.get('arquivo_excel')
            if arquivo_excel_b64:
                import tempfile
                import os
                import base64
                
                try:
                    # Decodifica base64 para arquivo temporário
                    file_data = base64.b64decode(arquivo_excel_b64)
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                        temp_file.write(file_data)
                        parameters["arquivo_excel"] = temp_file.name
                        temp_file_path = temp_file.name
                        print(f"✅ Arquivo salvo: {temp_file.name}")
                except Exception as e:
                    print(f"❌ Erro ao processar arquivo base64: {e}")
                    return {"error": "Arquivo base64 inválido"}, 400
            
            # Processa lista de lojas
            lojas_input = json_data.get('lojas', [])
            print(f"🔍 Lojas input: {lojas_input} (tipo: {type(lojas_input)})")
            
            # Garantia absoluta de que lojas será uma lista
            lojas = []
            if lojas_input:
                if isinstance(lojas_input, list):
                    lojas = [str(loja).strip() for loja in lojas_input if loja is not None and str(loja).strip()]
                elif isinstance(lojas_input, str) and lojas_input.strip():
                    lojas = [loja.strip() for loja in lojas_input.split(',') if loja.strip()]
            
            parameters["lojas"] = lojas
            print(f"✅ Lojas processadas: {lojas}")
            
            # Processa outros parâmetros string
            string_params = ['data', 'url', 'pasta_destino', 'data_inicio', 'data_fim', 'filial', 'modo']
            for param in string_params:
                value = json_data.get(param)
                if value is not None:
                    parameters[param] = str(value)
                    print(f"✅ Parâmetro {param}: {value}")
            
            print(f"✅ Todos os parâmetros: {parameters}")
            
            # 3. CRIAR EXECUÇÃO
            execution_id = ExecutionService.create_execution(
                automation_id=automation_id,
                triggered_by=getattr(request, 'user_id', Data.user_system())
            )

            print(f"📝 Execução criada: {execution_id}")
            
            # 4. FACTORY - CÓDIGO SIMPLIFICADO
            print(f"🎯 Identificando automação para: {automation.script_path}")
            
            command = None
            script_lower = (automation.script_path or "").lower()
            
            if 'pan' in script_lower or 'pan' in automation_id.lower():
                print("🚀 Criando PanService...")
                from APP.Services.pan_service import PanService
                command = PanService()
            elif 'fidc' in script_lower or 'fidc' in automation_id.lower():
                print("🚀 Criando FIDCAutomation...")
                from APP.Services.fidc_service import FIDCAutomation
                command = FIDCAutomation()
            else:
                print(f"❌ Tipo não identificado: {automation.script_path}")
            
            if not command:
                error_msg = f"Tipo de automação não suportado: {automation.script_path}"
                print(f"❌ {error_msg}")
                ExecutionService.fail_execution(execution_id, error_msg)
                return {"error": error_msg}, 404
            
            print(f"✅ Command criado: {type(command).__name__}")
            
            # 5. VALIDAR E EXECUTAR
            print("🔍 Validando parâmetros...")
            if not command.validate_parameters(parameters):
                error_msg = "Parâmetros inválidos para esta automação"
                print(f"❌ {error_msg}")
                ExecutionService.fail_execution(execution_id, error_msg)
                return {"error": error_msg}, 400
            
            print("🚀 Executando automação...")
            resultado = command.execute(parameters)
            print(f"✅ Automação concluída. Resultado: {resultado}")
            
            ExecutionService.complete_execution(execution_id, resultado)
            
            # Limpeza
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    print("✅ Arquivo temporário removido")
                except Exception as e:
                    print(f"⚠️ Erro ao remover arquivo: {e}")
            
            # Retorno
            execution = Execution.query.get(execution_id)
            return {
                "runId": execution_id,
                "automationId": automation_id,
                "status": execution.status,
                "startedAt": execution.start_time.isoformat() if execution.start_time else None,
                "finishedAt": execution.end_time.isoformat() if execution.end_time else None,
                "output": resultado,
            }, HTTPStatus.ACCEPTED
            
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            import traceback
            print(f"❌ Traceback: {traceback.format_exc()}")
            
            if execution_id:
                ExecutionService.fail_execution(execution_id, str(e))
            
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    print("✅ Arquivo temporário removido após erro")
                except:
                    pass
            
            db.session.rollback()
            return {"error": str(e)}, 500
        
# ===== /automation/ (ping) =====
automation_model = auto_ns.model("Automation", {
    "id":          fields.String(required=True),
    "name":        fields.String(required=True),
    "description": fields.String,
})


@auto_ns.route("/")
class AutomationRoot(ProtectedResource):
    @auto_ns.marshal_list_with(automation_model, code=HTTPStatus.OK, envelope=None)
    def get(self):
        # pegue só as colunas que vai expor
        rows = db.session.query(Automation.id, Automation.name, Automation.description)\
                         .limit(5).all()
        data = [{"id": str(i), "name": n, "description": d} for (i, n, d) in rows]
        current_app.logger.info("[AUTOMATIONS] Amostra IDs: %s", [d["id"] for d in data])
        return data, HTTPStatus.OK

@auto_ns.route("/status/<string:department_id>/<string:automation_id>")
class AutomationStatus(ProtectedResource):
    def get(self, department_id: str, automation_id: str):
        try:
            print(f"🔍 Buscando status: department={department_id}, automation={automation_id}")
            
            # Busca a ÚLTIMA execução específica (apenas 1)
            last_execution = db.session.query(Execution).filter(
                Execution.automation_id == automation_id
            ).order_by(Execution.start_time.desc()).first()
            
            if last_execution:
                print(f"✅ Última execução encontrada: {last_execution.status}")
                
                return {
                    "department_id": department_id,
                    "automation_id": automation_id,
                    "automation_name": last_execution.automation.name if last_execution.automation else "N/A",
                    "status": last_execution.status,
 
                }, HTTPStatus.OK
            else:
                print(f"⚠️  Nenhuma execução encontrada para {automation_id}")
                
                return {
                    "department_id": department_id,
                    "automation_id": automation_id,
                    "status": "never_executed",
                    "message": "Esta automação nunca foi executada"
                }, HTTPStatus.OK
                
        except Exception as e:
            print(f"❌ Erro ao buscar status: {e}")
            db.session.rollback()
            return {"error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR
    



