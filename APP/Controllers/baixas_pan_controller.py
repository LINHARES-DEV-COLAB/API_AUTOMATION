from flask import request, send_file
import os
import uuid
from werkzeug.utils import secure_filename
from flask_restx import Namespace, Resource, fields
from APP.Services.baixas_pan_service import pan_service
from APP.common.protected_resource import ProtectedResource
from ..Models.schemas import ProcessamentoRequest, ProcessamentoResponse, StatusProcessamento
from ..Config.settings import config

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

@baixas_pan_ns.route('/upload')
class UploadArquivo(ProtectedResource):
    @baixas_pan_ns.expect(upload_model)
    def post(self):
        """Upload de arquivo Excel para processamento"""
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

@baixas_pan_ns.route('/status/<string:job_id>')
class StatusProcessamento(ProtectedResource):
    def get(self, job_id):
        """Consultar status do processamento"""
        job = pan_service.get_job_status(job_id)
        if not job:
            return {'error': 'Job não encontrado'}, 404
        
        status = StatusProcessamento(
            job_id=job.job_id,
            status=job.status,
            progresso=job.progresso,
            mensagem=job.mensagem
        )
        
        return status.to_dict()

@baixas_pan_ns.route('/download/<string:job_id>/resultado')
class DownloadResultado(ProtectedResource):
    def get(self, job_id):
        """Download do arquivo CSV com resultados"""
        job = pan_service.get_job_status(job_id)
        if not job or not job.arquivo_resultado:
            return {'error': 'Arquivo de resultado não encontrado'}, 404
        
        if os.path.exists(job.arquivo_resultado):
            return send_file(
                job.arquivo_resultado,
                as_attachment=True,
                download_name=os.path.basename(job.arquivo_resultado)
            )
        
        return {'error': 'Arquivo não encontrado'}, 404

@baixas_pan_ns.route('/download/<string:job_id>/nao-encontrados')
class DownloadNaoEncontrados(ProtectedResource):
    def get(self, job_id):
        """Download do arquivo TXT com não encontrados"""
        job = pan_service.get_job_status(job_id)
        if not job or not job.arquivo_nao_encontrados:
            return {'error': 'Arquivo de não encontrados não encontrado'}, 404
        
        if os.path.exists(job.arquivo_nao_encontrados):
            return send_file(
                job.arquivo_nao_encontrados,
                as_attachment=True,
                download_name=os.path.basename(job.arquivo_nao_encontrados)
            )
        
        return {'error': 'Arquivo não encontrado'}, 404

@baixas_pan_ns.route('/datas-disponiveis')
class DatasDisponiveis(ProtectedResource):
    def get(self):
        """Listar datas disponíveis para busca"""
        # Implementar lógica para listar pastas disponíveis
        datas = ["01-01-2024", "02-01-2024", "03-01-2024"]  # Exemplo
        return {'datas_disponiveis': datas}