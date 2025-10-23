from flask import request, send_file
import os
import uuid
from werkzeug.utils import secure_filename
from flask_restx import Namespace, Resource, fields
from APP.Services.baixas_pan_service import pan_service
from APP.common.protected_resource import ProtectedResource
from ..Models.schemas import ProcessamentoRequest, ProcessamentoResponse, StatusProcessamento
from ..Config.settings import config
import io

# ✅ Mudar de Blueprint para Namespace
baixas_pan_ns = Namespace('baixas-pan', description='Operações de baixas bancárias PAN')

# Model para documentação Swagger
upload_model = baixas_pan_ns.model('UploadPAN', {
    'file': fields.Raw(description='Arquivo Excel', required=True),
    'banco': fields.String(default='PAN', description='Banco'),
    'datas_para_buscar': fields.String(description='Datas separadas por vírgula'),
    'tolerancia': fields.Float(default=0.10, description='Tolerância')
})

processamento_model = baixas_pan_ns.model('ProcessamentoPAN', {
    'arquivo_path': fields.String(required=True, description='Caminho do arquivo'),
    'banco': fields.String(default='PAN', description='Banco'),
    'datas_para_buscar': fields.List(fields.String, description='Datas para busca'),
    'tolerancia': fields.Float(default=0.10, description='Tolerância')
})

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@baixas_pan_ns.route('/processar-completo')
class ProcessarCompletoPAN(ProtectedResource):
    @baixas_pan_ns.expect(upload_model)
    def post(self):
        """
        Processamento completo em uma única rota
        - Upload do arquivo
        - Processamento dos dados
        - Retorno dos resultados
        """
        if 'file' not in request.files:
            return {'error': 'Nenhum arquivo enviado'}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {'error': 'Nenhum arquivo selecionado'}, 400
        
        if not file or not allowed_file(file.filename):
            return {'error': 'Tipo de arquivo não permitido'}, 400
        
        # Parâmetros do processamento
        banco = request.form.get('banco', 'PAN')
        datas_para_buscar_str = request.form.get('datas_para_buscar', '')
        datas_para_buscar = [data.strip() for data in datas_para_buscar_str.split(',')] if datas_para_buscar_str else []
        tolerancia = float(request.form.get('tolerancia', 0.10))
        
        # Processamento síncrono
        resultado = pan_service.processar_arquivo_sincrono(
            file_stream=file,
            filename=file.filename,
            banco=banco,
            datas_para_buscar=datas_para_buscar,
            tolerancia=tolerancia
        )
        
        if resultado['status'] == 'erro':
            return {'error': resultado['mensagem']}, 500
        
        # Retornar resultados diretamente
        return {
            'status': 'concluido',
            'mensagem': 'Processamento concluído com sucesso',
            'total_processado': resultado['total_processado'],
            'total_nao_encontrados': resultado['total_nao_encontrados'],
            'resultados': resultado['resultados_csv'],
            'nao_encontrados': resultado['nao_encontrados_txt']
        }, 200

# Mantenha as rotas existentes para compatibilidade
@baixas_pan_ns.route('/upload')
class UploadArquivo(ProtectedResource):
    @baixas_pan_ns.expect(upload_model)
    def post(self):
        """Upload de arquivo Excel para processamento (assíncrono)"""
        if 'file' not in request.files:
            return {'error': 'Nenhum arquivo enviado'}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {'error': 'Nenhum arquivo selecionado'}, 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = config.UPLOAD_DIR / filename
            file.save(file_path)
            
            # Parâmetros do processamento
            banco = request.form.get('banco', 'PAN')
            datas_para_buscar = request.form.get('datas_para_buscar', '').split(',')
            tolerancia = float(request.form.get('tolerancia', 0.10))
            
            # Iniciar processamento
            response = pan_service.iniciar_processamento(
                arquivo_path=str(file_path),
                banco=banco,
                datas_para_buscar=datas_para_buscar,
                tolerancia=tolerancia
            )
            
            return response.to_dict(), 202
        
        return {'error': 'Tipo de arquivo não permitido'}, 400

# ... (mantenha as outras rotas existentes para compatibilidade)
@baixas_pan_ns.route('/processar')
class ProcessarPAN(ProtectedResource):
    @baixas_pan_ns.expect(processamento_model)
    def post(self):
        """Processar arquivo PAN (já upload)"""
        data = request.get_json()
        
        if not data or 'arquivo_path' not in data:
            return {'error': 'Caminho do arquivo é obrigatório'}, 400
        
        response = pan_service.iniciar_processamento(
            arquivo_path=data['arquivo_path'],
            banco=data.get('banco', 'PAN'),
            datas_para_buscar=data.get('datas_para_buscar', []),
            tolerancia=data.get('tolerancia', 0.10)
        )
        
        return response.to_dict(), 202

# ... (mantenha as rotas de status, download, etc.)