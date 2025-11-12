import pandas as pd
import logging
import os
import re

logger = logging.getLogger(__name__)

class AymoreService:
    def __init__(self):
        print("✅ AymoreService inicializado")

    def processar_aymore(self, path: str) -> list:
        """
        Processa arquivo Excel e extrai TODOS os códigos especiais em uma única lista
        """
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Arquivo não encontrado: {path}")
            
            print(f"📁 Processando: {path}")
            print("=" * 100)
            
            # Ler arquivo completo
            df = pd.read_excel(path, sheet_name='Sheet0')
            
            # Processar dados e extrair TODOS os códigos em uma lista
            resultado = self._processar_e_extrair_lista_unica(df, path)
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro no processamento: {str(e)}")
            raise e

    def _extrair_codigos_especiais(self, historico: str) -> list:
        """
        Extrai TODOS os códigos especiais de QUALQUER histórico
        """
        if not isinstance(historico, str):
            return []
        
        codigos_encontrados = []
        
        # Split por espaços para analisar cada token
        tokens = historico.split()
        
        for token in tokens:
            # Limpar o token (remover pontuação no início/fim)
            token_limpo = token.strip('.,;:!?()[]{}"\'')
            
            # PADRÃO 1: Códigos que começam com 9C2
            if (token_limpo.startswith('9C2') and 
                len(token_limpo) >= 10 and
                any(c.isalpha() for c in token_limpo) and
                any(c.isdigit() for c in token_limpo)):
                codigos_encontrados.append(token_limpo)
            
            # PADRÃO 2: Códigos que contém TR, RR, LR
            elif (any(marker in token_limpo for marker in ['TR', 'RR', 'LR', 'CR', 'DR']) and
                  len(token_limpo) >= 10 and
                  any(c.isalpha() for c in token_limpo) and
                  any(c.isdigit() for c in token_limpo)):
                codigos_encontrados.append(token_limpo)
            
            # PADRÃO 3: Códigos que começam com RES
            elif (token_limpo.startswith('RES') and 
                  len(token_limpo) >= 10 and
                  any(c.isdigit() for c in token_limpo)):
                codigos_encontrados.append(token_limpo)
            
            # PADRÃO 4: Sequências alfanuméricas longas (backup)
            elif (len(token_limpo) >= 8 and
                  any(c.isalpha() for c in token_limpo) and
                  any(c.isdigit() for c in token_limpo) and
                  not token_limpo.isdigit() and
                  not token_limpo.isalpha() and
                  not any(ext in token_limpo.lower() for ext in ['.com', '.br', 'http', 'www'])):
                codigos_encontrados.append(token_limpo)
        
        return list(set(codigos_encontrados))

    def _processar_e_extrair_lista_unica(self, df: pd.DataFrame, path: str) -> dict:
        """Processa dados e extrai TODOS os códigos em UMA LISTA ÚNICA"""
        
        print("\n🎯 **EXTRAINDO TODOS OS CÓDIGOS ESPECIAIS - LISTA ÚNICA**")
        print("=" * 100)
        
        # Limpeza inicial
        df_clean = df.dropna(how='all')
        
        # Encontrar linha do cabeçalho real
        header_idx = None
        for idx, row in df_clean.iterrows():
            if len(row) > 0 and 'Data' in str(row.iloc[0]):
                header_idx = idx
                break
        
        # Reorganizar DataFrame
        if header_idx is not None:
            headers = [str(h) if pd.notna(h) else f'Coluna_{i}' for i, h in enumerate(df_clean.iloc[header_idx])]
            df_data = df_clean.iloc[header_idx + 1:].copy()
            df_data.columns = headers
            df_clean = df_data
        
        # Renomear colunas
        if len(df_clean.columns) >= 6:
            novos_nomes = ['Data', 'Vazio', 'Historico', 'Documento', 'Valor_RS', 'Saldo_RS']
            df_clean.columns = novos_nomes[:len(df_clean.columns)]
            if 'Vazio' in df_clean.columns:
                df_clean = df_clean.drop('Vazio', axis=1)
        
        # Filtrar e processar
        mask = (df_clean['Data'].notna()) & (df_clean['Data'].astype(str) != '')
        df_transactions = df_clean[mask].copy()
        
        df_transactions['Data'] = pd.to_datetime(df_transactions['Data'], errors='coerce')
        df_transactions['Valor_RS'] = pd.to_numeric(df_transactions['Valor_RS'], errors='coerce')
        df_transactions = df_transactions[df_transactions['Data'].notna()]
        
        # EXTRAIR CÓDIGOS DE TODOS OS HISTÓRICOS - LISTA ÚNICA
        print("\n🔍 **TODOS OS CÓDIGOS ENCONTRADOS:**")
        print("=" * 80)
        
        lista_unica_codigos = []
        
        for idx, transacao in df_transactions.iterrows():
            historico = str(transacao['Historico'])
            data = transacao['Data'].strftime('%d/%m/%Y')
            valor = transacao['Valor_RS']
            
            codigos = self._extrair_codigos_especiais(historico)
            
            if codigos:
                for codigo in codigos:
                    print(f"📋 {data} | R$ {valor:>10,.2f} | {codigo} | {historico}")
                    lista_unica_codigos.append({
                        'data': data,
                        'valor': valor,
                        'codigo': codigo,
                        'historico_completo': historico
                    })
        
        # MOSTRAR LISTA ÚNICA COMPLETA
        print(f"\n📋 **LISTA ÚNICA DE TODOS OS CÓDIGOS ({len(lista_unica_codigos)} itens):**")
        print("=" * 70)
        
        for i, item in enumerate(lista_unica_codigos, 1):
            print(f"{i:2d}. {item['codigo']} | {item['data']} | R$ {item['valor']:>10,.2f}")
        
        # ESTATÍSTICAS SIMPLES
        print(f"\n📊 **ESTATÍSTICAS:**")
        print("=" * 40)
        
        if lista_unica_codigos:
            todos_codigos = [item['codigo'] for item in lista_unica_codigos]
            codigos_unicos = list(set(todos_codigos))
            
            print(f"📈 Total de ocorrências: {len(lista_unica_codigos)}")
            print(f"🔤 Códigos únicos: {len(codigos_unicos)}")
            
            # Valores totais
            valor_total = sum(item['valor'] for item in lista_unica_codigos)
            print(f"💰 Valor total envolvido: R$ {valor_total:,.2f}")
            
            # Top 5 códigos por valor
            print(f"\n🏆 TOP 5 CÓDIGOS POR VALOR:")
            top5 = sorted(lista_unica_codigos, key=lambda x: abs(x['valor']), reverse=True)[:5]
            for i, item in enumerate(top5, 1):
                print(f"   {i}. {item['codigo']} | R$ {item['valor']:>10,.2f}")
        
        # Salvar CSV com lista única
        output_path = 'extracao_transacoes.csv'
        df_transactions.to_csv(output_path, index=False, encoding='utf-8')
        
        # Criar CSV apenas com a lista de códigos
        df_codigos = pd.DataFrame(lista_unica_codigos)
        if not df_codigos.empty:
            df_codigos.to_csv('lista_unica_codigos.csv', index=False, encoding='utf-8')
            print(f"\n💾 Lista única salva: lista_unica_codigos.csv")
        
        return {
            "status": "sucesso",
            "total_transacoes": len(df_transactions),
            "total_codigos_encontrados": len(lista_unica_codigos),
            "codigos_unicos": len(set([item['codigo'] for item in lista_unica_codigos])),
            "valor_total_codigos": sum(item['valor'] for item in lista_unica_codigos),
            "lista_codigos": lista_unica_codigos,
            "arquivo_entrada": os.path.basename(path),
            "arquivo_saida": output_path
        }