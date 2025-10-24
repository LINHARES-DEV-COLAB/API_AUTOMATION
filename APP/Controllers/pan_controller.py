from flask import request
from flask_restx import Namespace, Resource, fields
import tempfile
import os
from APP.Services.pan_service import PanService

# Define namespace
baixas_pan_ns = Namespace('baixas-pan', description='Operações para processamento de baixas PAN')

# Model para documentação da API
upload_model = baixas_pan_ns.model('UploadExtrato', {
    'file': fields.Raw(description='Arquivo Excel do extrato Itaú', required=True)
})

result_model = baixas_pan_ns.model('ResultadoPan', {
    'TITULO': fields.String(description='Número do título'),
    'DUPLICATA': fields.String(description='Número da duplicata'),
    'VALOR': fields.String(description='Valor do título')
})

@baixas_pan_ns.route('/processar-extrato')
class ProcessarExtratoPan(Resource):
    @baixas_pan_ns.expect(upload_model)
    @baixas_pan_ns.response(200, 'Sucesso', [result_model])
    @baixas_pan_ns.response(400, 'Arquivo inválido')
    @baixas_pan_ns.response(500, 'Erro interno')
    def post(self):
        """
        Processa extrato Itaú para identificar baixas PAN
        
        Parâmetros:
        - file: Arquivo Excel do extrato Itaú (obrigatório)
        - data: Data para busca no formato DD-MM-AAAA (opcional, padrão: data atual)
        """
        try:
            # DEBUG DETALHADO - Ver todos os parâmetros recebidos
            print(f"🎯 DEBUG COMPLETO DA REQUISIÇÃO:")
            print(f"   Content-Type: {request.content_type}")
            print(f"   Form data: {dict(request.form)}")
            print(f"   Files: {list(request.files.keys())}")
            print(f"   Args: {dict(request.args)}")
            print(f"   Headers: {dict(request.headers)}")
        
        # Verifique TODOS os campos do form
            for key in request.form:
                print(f"   📋 Form field '{key}': '{request.form[key]}'")
            
            # Verifica se o arquivo foi enviado
            if 'file' not in request.files:
                return {'error': 'Nenhum arquivo enviado'}, 400
            
            file = request.files['file']
            
            if file.filename == '':
                return {'error': 'Nome de arquivo vazio'}, 400
            
            # Verifica extensão do arquivo
            if not file.filename.lower().endswith(('.xlsx', '.xls')):
                return {'error': 'Tipo de arquivo não permitido. Use .xlsx ou .xls'}, 400
            
            # Obtém a data do parâmetro (de várias fontes possíveis)
            data_param = request.form.get('data') or request.args.get('data')
            print(f"📅 DATA CAPTURADA: '{data_param}'")
            
            if not data_param:
                print("⚠️  ATENÇÃO: Nenhuma data foi enviada na requisição!")
            
            # Salva o arquivo temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                file.save(temp_file.name)
                temp_path = temp_file.name
            
            try:
                # Processa o extrato PASSANDO A DATA para o método principal
                pan_service = PanService()
                
                # SEMPRE chama o método principal, passando a data como parâmetro
                resultados = pan_service.processar_extrato(temp_path, data_param)
                
                if not resultados:
                    return {'message': 'Nenhum lançamento PAN encontrado no extrato'}, 404
                
                # Converte para lista de dicionários
                dados_resultado = [resultado.to_dict() for resultado in resultados]
                
                return {
                    'message': f'Processamento concluído - {len(dados_resultado)} registros encontrados',
                    'data': dados_resultado,
                    'data_busca': data_param or 'automática'
                }, 200
                
            finally:
                # Limpa arquivo temporário
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            return {'error': f'Erro no processamento: {str(e)}'}, 500
@baixas_pan_ns.route('/health')
class HealthCheck(Resource):
    def get(self):
        """
        Health check do serviço PAN
        """
        return {
            'status': 'ok',
            'service': 'Baixas PAN',
            'message': 'Serviço funcionando corretamente'
        }