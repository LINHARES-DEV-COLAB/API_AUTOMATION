import pandas as pd
import uuid
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename

from ..Core.pan_processor import PanProcessor
from APP.DTO.pan import ProcessamentoJob
from ..Models.schemas import ProcessamentoResponse, StatusProcessamento
from ..Config.settings import config

logger = logging.getLogger(__name__)

class PanService:
    def __init__(self):
        self.jobs: Dict[str, ProcessamentoJob] = {}
        self.processor = PanProcessor()
    
    def iniciar_processamento(self, arquivo_path: str, banco: str = "PAN", 
                            datas_para_buscar: List[str] = None, tolerancia: float = 0.10) -> ProcessamentoResponse:
        job_id = str(uuid.uuid4())
        job = ProcessamentoJob(job_id)
        self.jobs[job_id] = job
        
        # Processamento em thread (simulado)
        import threading
        thread = threading.Thread(
            target=self._processar_async,
            args=(job, arquivo_path, banco, datas_para_buscar or [], tolerancia)
        )
        thread.daemon = True
        thread.start()
        
        return ProcessamentoResponse(
            job_id=job.job_id,
            status=job.status,
            mensagem=job.mensagem
        )
    
    def processar_arquivo_sincrono(self, file_stream, filename: str, banco: str = "PAN", 
                                 datas_para_buscar: List[str] = None, tolerancia: float = 0.10) -> Dict[str, Any]:
        """Processa o arquivo de forma síncrona e retorna os resultados"""
        try:
            # Salvar arquivo temporariamente
            filename = secure_filename(filename)
            file_path = config.UPLOAD_DIR / f"temp_{uuid.uuid4()}_{filename}"
            file_stream.save(file_path)
            
            # Processar arquivo PAN
            resultados = self.processor.processar_pan_multidata(
                caminho_arquivo=str(file_path),
                base_dir_rede=self.processor.pan_network_path,
                datas_para_buscar=datas_para_buscar or [],
                atol=tolerancia
            )
            
            # Gerar arquivos de resultado
            arquivo_resultado = self._salvar_resultados_csv(resultados)
            arquivo_nao_encontrados = self._salvar_nao_encontrados_txt(resultados)
            
            # Ler conteúdo dos arquivos
            with open(arquivo_resultado, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            with open(arquivo_nao_encontrados, 'r', encoding='utf-8') as f:
                txt_content = f.read()
            
            # Limpar arquivos temporários
            try:
                os.remove(file_path)
                os.remove(arquivo_resultado)
                os.remove(arquivo_nao_encontrados)
            except Exception as e:
                logger.warning(f"Erro ao limpar arquivos temporários: {e}")
            
            return {
                'status': 'concluido',
                'resultados_csv': csv_content,
                'nao_encontrados_txt': txt_content,
                'total_processado': len(resultados.get('encontrados', [])),
                'total_nao_encontrados': len(resultados.get('nao_encontrados', []))
            }
            
        except Exception as e:
            # Limpar arquivo temporário em caso de erro
            try:
                if 'file_path' in locals() and os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
                
            logger.error(f"Erro no processamento síncrono: {e}")
            return {
                'status': 'erro',
                'mensagem': f"Erro no processamento: {str(e)}"
            }
    
    def _processar_async(self, job: ProcessamentoJob, arquivo_path: str, banco: str, 
                        datas_para_buscar: List[str], tolerancia: float):
        try:
            job.status = "processando"
            job.progresso = 10
            job.mensagem = "Iniciando processamento..."
            
            # Processar arquivo PAN
            resultados = self.processor.processar_pan_multidata(
                caminho_arquivo=arquivo_path,
                base_dir_rede=self.processor.pan_network_path,
                datas_para_buscar=datas_para_buscar,
                atol=tolerancia
            )
            
            job.progresso = 80
            job.mensagem = "Gerando arquivos de resultado..."
            
            # Salvar resultados
            job.arquivo_resultado = self._salvar_resultados_csv(resultados)
            job.arquivo_nao_encontrados = self._salvar_nao_encontrados_txt(resultados)
            
            job.status = "concluido"
            job.progresso = 100
            job.mensagem = "Processamento concluído com sucesso"
            
        except Exception as e:
            job.status = "erro"
            job.mensagem = f"Erro no processamento: {str(e)}"
            logger.error(f"Erro no job {job.job_id}: {e}")
    
    def _salvar_resultados_csv(self, resultados):
        # Implementar lógica de salvamento
        output_path = config.UPLOAD_DIR / f"resultado_{uuid.uuid4()}.csv"
        
        # Converter resultados para DataFrame e salvar como CSV
        if 'encontrados' in resultados and resultados['encontrados']:
            df = pd.DataFrame(resultados['encontrados'])
            df.to_csv(output_path, index=False, encoding='utf-8')
        
        return str(output_path)
    
    def _salvar_nao_encontrados_txt(self, resultados):
        # Implementar lógica de salvamento
        output_path = config.UPLOAD_DIR / f"nao_encontrados_{uuid.uuid4()}.txt"
        
        # Salvar não encontrados em arquivo texto
        with open(output_path, 'w', encoding='utf-8') as f:
            if 'nao_encontrados' in resultados:
                for item in resultados['nao_encontrados']:
                    f.write(f"{item}\n")
        
        return str(output_path)
    
    def get_job_status(self, job_id: str) -> ProcessamentoJob:
        return self.jobs.get(job_id)

pan_service = PanService()