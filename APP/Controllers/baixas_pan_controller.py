from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required
import tempfile
import os

from APP.Services.baixas_pan_service import BaixasPanService

# Namespace
baixas_pan_ns = Namespace('baixas-pan', description='Operações de baixas bancárias PAN')

# Models para documentação Swagger
processar_extrato_input = baixas_pan_ns.model('ProcessarExtratoInput', {
    'file': fields.Raw(required=True, description='Arquivo Excel do extrato bancário')
})

busca_direta_input = baixas_pan_ns.model('BuscaDiretaInput', {
    'valores': fields.List(fields.Float, required=True, description='Lista de valores para buscar'),
    'datas': fields.List(fields.String, description='Datas específicas para buscar (opcional)')
})

resultado_item = baixas_pan_ns.model('ResultadoItem', {
    '__Arquivo__': fields.String,
    '__Planilha__': fields.String,
    '__Coluna_Encontrado__': fields.String,
    '__VALOR_NUM__': fields.Float,
    '__VALOR_ORIGINAL__': fields.Float,
    '__TITULO__': fields.String,
    '__DUPLICATA__': fields.String,
    '__VALOR_TITULO__': fields.Float,
    '__DATA_ORIGEM__': fields.String
})

estatisticas_model = baixas_pan_ns.model('Estatisticas', {
    'valores_extraidos': fields.Integer,
    'valores_encontrados': fields.Integer,
    'valores_nao_encontrados': fields.Integer,
    'total_registros': fields.Integer,
    'datas_buscadas': fields.List(fields.String),
    'datas_com_resultados': fields.List(fields.String)
})

resposta_sucesso = baixas_pan_ns.model('RespostaSucesso', {
    'sucesso': fields.Boolean,
    'estatisticas': fields.Nested(estatisticas_model),
    'valores_extraidos': fields.List(fields.Float),
    'valores_nao_encontrados': fields.List(fields.Float),
    'resultados': fields.List(fields.Nested(resultado_item)),
    'timestamp': fields.String
})

resposta_erro = baixas_pan_ns.model('RespostaErro', {
    'sucesso': fields.Boolean,
    'erro': fields.String
})

class ProtectedResource(Resource):
    """Base que protege todos os métodos da resource com JWT."""
    method_decorators = [jwt_required()]

@baixas_pan_ns.route('/processar-extrato')
class ProcessarExtrato(ProtectedResource):
    @baixas_pan_ns.doc(description='Processa arquivo de extrato e busca correspondências nos arquivos PAN')
    @baixas_pan_ns.expect(processar_extrato_input)
    @baixas_pan_ns.response(200, 'Sucesso', resposta_sucesso)
    @baixas_pan_ns.response(400, 'Erro', resposta_erro)
    @baixas_pan_ns.response(500, 'Erro interno', resposta_erro)
    def post(self):
        """Processa arquivo de extrato bancário"""
        try:
            # Verificar se o arquivo foi enviado
            if 'file' not in request.files:
                return {'sucesso': False, 'erro': 'Nenhum arquivo enviado'}, 400
            
            file = request.files['file']
            if file.filename == '':
                return {'sucesso': False, 'erro': 'Nome de arquivo vazio'}, 400
            
            # Validar extensão
            if not file.filename.lower().endswith(('.xlsx', '.xls')):
                return {'sucesso': False, 'erro': 'Arquivo deve ser Excel (.xlsx ou .xls)'}, 400
            
            # Salvar arquivo temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                file.save(tmp_file.name)
                caminho_arquivo = tmp_file.name
            
            try:
                # Chamar service
                service = BaixasPanService()
                resultado = service.processar_extrato(caminho_arquivo)
                
                # Retornar resultado
                status_code = 200 if resultado['sucesso'] else 400
                return resultado, status_code
                
            finally:
                # Limpar arquivo temporário
                if os.path.exists(caminho_arquivo):
                    os.unlink(caminho_arquivo)
                    
        except Exception as e:
            current_app.logger.error(f'Erro em processar-extrato: {str(e)}')
            return {'sucesso': False, 'erro': f'Erro interno: {str(e)}'}, 500

@baixas_pan_ns.route('/busca-direta')
class BuscaDireta(ProtectedResource):
    @baixas_pan_ns.doc(description='Busca direta por valores específicos nos arquivos PAN')
    @baixas_pan_ns.expect(busca_direta_input)
    @baixas_pan_ns.response(200, 'Sucesso', resposta_sucesso)
    @baixas_pan_ns.response(400, 'Erro', resposta_erro)
    def post(self):
        """Busca direta por valores"""
        try:
            dados = request.get_json()
            valores = dados.get('valores', [])
            datas = dados.get('datas', [])
            
            if not valores:
                return {'sucesso': False, 'erro': 'Nenhum valor fornecido para busca'}, 400
            
            # Chamar service
            service = BaixasPanService()
            resultado = service.buscar_valores_diretos(valores, datas)
            
            status_code = 200 if resultado['sucesso'] else 400
            return resultado, status_code
            
        except Exception as e:
            current_app.logger.error(f'Erro em busca-direta: {str(e)}')
            return {'sucesso': False, 'erro': f'Erro interno: {str(e)}'}, 500

@baixas_pan_ns.route('/pastas-disponiveis')
class PastasDisponiveis(ProtectedResource):
    @baixas_pan_ns.doc(description='Lista as pastas PAN disponíveis na rede')
    @baixas_pan_ns.response(200, 'Sucesso')
    def get(self):
        """Lista pastas disponíveis"""
        try:
            service = BaixasPanService()
            resultado = service.listar_pastas_disponiveis()
            
            status_code = 200 if resultado['sucesso'] else 400
            return resultado, status_code
            
        except Exception as e:
            current_app.logger.error(f'Erro em pastas-disponiveis: {str(e)}')
            return {'sucesso': False, 'erro': f'Erro interno: {str(e)}'}, 500

@baixas_pan_ns.route('/health')
class HealthCheck(Resource):
    @baixas_pan_ns.doc(description='Verifica saúde do serviço PAN')
    def get(self):
        """Health check"""
        return {
            'status': 'online',
            'servico': 'baixas-pan',
            'timestamp': '2024-01-01T00:00:00'  # Você pode usar datetime aqui
        }, 200