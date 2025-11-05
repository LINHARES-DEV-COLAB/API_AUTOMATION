from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from openpyxl import load_workbook, Workbook
from dotenv import load_dotenv
from tkinter import messagebox
from pathlib import Path as P
from datetime import datetime
from time import sleep
import pandas as pd
import pdfplumber
import oracledb
import random
import os

load_dotenv()

user_oracle = os.getenv('USER_ORACLE')
password = os.getenv('PASSWORD_ORACLE')
dsn = os.getenv('DSN')


def connection():
    """
    Cria uma conexão com o banco de dados Oracle.

    Parâmetros:
        None

    Retorno:
        oracledb.Connection: Objeto de conexão ativo com o banco de dados Oracle.
    """
    oracledb.init_oracle_client(
        lib_dir=r'C:\instantclient'
    )

    # Conexão com o Oracle
    return oracledb.connect(
        user=user_oracle,
        password=password,
        dsn=dsn
    )


def busca_dados_db(banco, empresa):
    conn = connection()

    try:
        cur = conn.cursor()

        cur.execute(
            f'''SELECT
                TITULO, DUPLICATA, VAL_TITULO, HISTORICO, ORIGEM, STATUS
            FROM
                FIN_TITULO
            WHERE
                TIPO = 'BC'
                AND STATUS <> 'CA'
                AND PAGAR_RECEBER = 'R'
                AND EMPRESA = {empresa}
                AND BANCO = {banco}
                AND ORIGEM IN (1258, 1282)
                AND DTA_EMISSAO = CASE
                    WHEN TO_CHAR(SYSDATE - 1, 'DY', 'NLS_DATE_LANGUAGE=ENGLISH') = 'SUN'
                        THEN TRUNC(SYSDATE) - 3  -- sexta-feira
                    ELSE TRUNC(SYSDATE) - 1      -- dia anterior normal
                END'''
        )

        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def busca_dados_db_por_um(empresa, titulo):
    conn = connection()

    try:
        cur = conn.cursor()

        cur.execute(
            f'''SELECT
                TITULO, DUPLICATA, VAL_TITULO, HISTORICO, ORIGEM, STATUS
            FROM
                FIN_TITULO
            WHERE
                TIPO = 'CR'
                AND STATUS <> 'CA'
                AND TITULO = {titulo}
                AND PAGAR_RECEBER = 'R'
                AND EMPRESA = {empresa}
                AND BANCO = 900
                AND ORIGEM IN (1258, 1282)'''
        )

        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def extract_text_pdfplumber(nome_loja, pdf_path):
    try:
        paginas = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                paginas.append(page.extract_text() or "")

        numero_nota = []
        valor = []
        grupo_cota_rd = []

        for i in range(len(paginas)):
            lista_linhas = paginas[i].split('\n')
            for j in lista_linhas:
                if 'LANC. PAGAMEN. AUTOM' in j:
                    texto_lista = str(j).split(sep=' ')
                    numero_nota.append(texto_lista[1])
                    valor.append(texto_lista[-2])

                    grupo = texto_lista[2].split(sep='/')
                    if len(grupo) < 4:
                        grupo_cota_rd.append(texto_lista[2] + texto_lista[3].strip())
                    else:
                        grupo_cota_rd.append(texto_lista[2])

        data = {
            'NUMERO NOTA': numero_nota,
            'VALOR': valor,
            'GRUPO COTA RD': grupo_cota_rd
        }

        df = pd.DataFrame(data, columns=['NUMERO NOTA', 'VALOR', 'GRUPO COTA RD'])

        caminho_excel = str(pdf_path).replace(f'{nome_loja}.pdf', f'extracao_pdf_{nome_loja}.xlsx')

        df.to_excel(caminho_excel, index=False)

        return True, 'Automação de extração de dados do pdf concluída.'
    except Exception as e:
        return False, f'Erro ao extrair os dados do pdf.\nDescrição: {str(e)}'


# mapeia loja -> (banco, empresa)
MAPA_EMPRESA = {
    "JUAZEIRO":     (21018, 2),
    "TERRA_SANTA":  (21018, 2),
    "CRATO":        (51017, 5),
    "ARACATI":      (31049, 3),
}

def verifica_dados_linx(loja: str, dir_path: str | os.PathLike):
    try:
        loja_u = loja.upper()
        if loja_u not in MAPA_EMPRESA:
            return False, f"Loja desconhecida: {loja}"

        banco, empresa = MAPA_EMPRESA[loja_u]

        # 1) monte o ARQUIVO correto e use-o no read_excel
        dir_path = P(dir_path)
        arquivo_origem = dir_path / f"extracao_pdf_{loja_u}.xlsx"
        if not arquivo_origem.exists():
            return False, f"Arquivo não encontrado: {arquivo_origem}"

        # 2) leia o Excel do ARQUIVO, não da pasta
        df_src = pd.read_excel(arquivo_origem, engine="openpyxl")

        # 3) prepare colunas de interesse
        numeros_notas_honda = df_src['NUMERO NOTA'].astype(str)
        valores_honda_comparar = [parse_valor(v.strip()) for v in df_src['VALOR'].astype(str)]

        titulos, duplicatas, valores_linx, valores_honda, tipos_ajustes, origens = ([] for _ in range(6))

        dados_linx = busca_dados_db(banco=banco, empresa=empresa)
        numeros_nota_linx = {}
        for dados in dados_linx:
            nota = str(dados[3]).replace(
                'LANCAMENTO BANCARIO REFERENTE PAGAMENTO TITULO (CR): ', ''
            ).split('-')[0]
            numeros_nota_linx[nota.strip()] = dados[4]
        
        vistos = set()  # armazena pares (titulo, origem)

        for titulo, valor in zip(numeros_notas_honda, valores_honda_comparar):
            if titulo not in numeros_nota_linx:
                nota_nao_paga = busca_dados_db_por_um(empresa=empresa, titulo=titulo)
                for nota in nota_nao_paga:
                    titulo_db   = nota[0]
                    duplicata   = nota[1]
                    valor_db    = nota[2]
                    origem_code = nota[-2]
                    origem_nome = 'CNH' if origem_code == 1258 else 'Plano Legal'
                    # Se já processou essa combinação, pula
                    if (titulo_db, origem_nome) in vistos:
                        continue
                    vistos.add((titulo_db, origem_nome))

                    tipo_ajuste = compara_valores(valor_db=valor_db, valor_honda=valor)
                    titulos.append(titulo_db)
                    duplicatas.append(duplicata)
                    valores_linx.append(parse_valor_string(valor_db))
                    valores_honda.append(parse_valor_string(valor))
                    tipos_ajustes.append(tipo_ajuste)
                    origens.append(origem_nome)

        # 4) DataFrames de saída
        df_csv = pd.DataFrame({
            'TITULO': titulos,
            'DUPLICATA': duplicatas,
            'VALOR': valores_linx
        })

        df_xlsx = pd.DataFrame({
            'TITULO': titulos,
            'DUPLICATA': duplicatas,
            'VALOR_LINX': valores_linx,
            'VALOR_HONDA': valores_honda,
            'TIPO DE AJUSTE': tipos_ajustes,
            'ORIGEM': origens,
        })

        hoje = datetime.now().strftime("%d-%m-%Y")

        # 5) Pastas de saída (garante existência)
        base_dir   = P(r"\\172.17.67.14\findev$\Automação - CNH\Preparação das Baixas")
        csv_dir    = base_dir / "Arquivos_csv"
        excel_dir  = base_dir / "Arquivos_excel"
        csv_dir.mkdir(parents=True, exist_ok=True)
        excel_dir.mkdir(parents=True, exist_ok=True)

        # 6) Nomes de arquivos (use a loja do parâmetro)
        nome_loja_out = loja_u
        out_csv  = csv_dir   / f"{nome_loja_out}_{hoje}.csv"
        out_xlsx = excel_dir / f"{nome_loja_out}_{hoje}.xlsx"

        # 7) Salvar
        df_csv.to_csv(out_csv, index=False, sep=';', encoding='utf-8-sig')
        df_xlsx.to_excel(out_xlsx, index=False)

        return True, "Automação de verificação de dados na linx realizada com sucesso."

    except Exception as e:
        return False, f"Erro ao verificar os dados da Linx.\nDescrição: {e}"


def parse_valor(valor_str: str) -> float:
    """
    Converte um número no formato brasileiro (1.234,56) para float.

    Parâmetros:
        valor_str (str): String com o valor monetário.

    Retorno:
        float: Valor convertido.
    """
    valor_str = valor_str.strip()
    if not valor_str:
        return 0.0
    return float(valor_str.replace('.', '').replace(',', '.'))

def parse_valor_string(valor_str: float) -> str:
    if not valor_str:
        return '0,0'
    return f'{valor_str:,.2f}'.replace('.', '_').replace(',', '.').replace('_', ',')

def _valor_aproximado(a, b) -> float:
    """
    Retorna (ok, diff).
    ok=True se |a-b| <= tol_abs OU (se tol_pct for definido) |a-b| <= base*tol_pct.
    """
    a = float(a)
    b = float(b)
    diff = abs(a - b)
    return diff

def compara_valores(
    valor_db: float,
    valor_honda: list
) -> float:
    # Match forte — compara valores com tolerância
    diff = _valor_aproximado(valor_db, valor_honda)
    if diff == 0:
        # valores idênticos
        return 'Sem ajustes'
    else:
        diff_real = parse_valor_string(diff)
        # dentro da tolerância → normaliza
        tipo_ajuste = f"+{diff_real}" if valor_honda > valor_db else f"-{diff_real}"
        return tipo_ajuste
    