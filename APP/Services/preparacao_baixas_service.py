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
                AND ORIGEM IN (1258, 1282)
                AND DTA_EMISSAO = CASE
                    WHEN TO_CHAR(SYSDATE - 1, 'DY', 'NLS_DATE_LANGUAGE=ENGLISH') = 'SUN'
                        THEN TRUNC(SYSDATE) - 3  -- sexta-feira
                    ELSE TRUNC(SYSDATE) - 1      -- dia anterior normal
                END'''
        )

        return cur.fetchone()
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


def verifica_dados_linx(path):
    try:
        nome_loja = str(path).split('_')[-1].replace('.xlsx', '')

        if 'JUAZEIRO' in nome_loja.upper():
            banco = 21018
            empresa = 2
        elif 'CRATO' in nome_loja.upper():
            banco = 21018
            empresa = 2
        elif 'ARACATI' in nome_loja.upper():
            banco = 51017
            empresa = 5
        elif 'INHAMUNS' in nome_loja.upper():
            banco = 31049
            empresa = 3
        
        arquivo_excel = pd.read_excel(io=path)

        numeros_notas_honda = arquivo_excel['NUMERO NOTA']
        valores_honda_comparar = [parse_valor(v.strip()) for v in arquivo_excel['VALOR']]

        titulos = []
        duplicatas = []
        valores_linx = []
        valores_honda = []
        tipos_ajustes = []
        origens = []

        dados_linx = busca_dados_db(banco=banco, empresa=empresa)
        numeros_nota_linx = []
        for dados in dados_linx:
            nota = str(dados[3]).replace('LANCAMENTO BANCARIO REFERENTE PAGAMENTO TITULO (CR): ', '').split('-')[0]
            numeros_nota_linx.append(str(nota).strip())

        for titulo, valor in zip(numeros_notas_honda, valores_honda_comparar):
            titulo = str(titulo)
            if titulo not in numeros_nota_linx:
                nota_nao_paga = busca_dados_db_por_um(empresa=empresa, titulo=titulo)
                if nota_nao_paga:
                    titulo_db = nota_nao_paga[0]
                    duplicata = nota_nao_paga[1]
                    valor_db = nota_nao_paga[2]
                    origem = nota_nao_paga[-2]

                    tipo_ajuste = compara_valores(valor_db=valor_db, valor_honda=valor)
                    titulos.append(titulo_db)
                    duplicatas.append(duplicata)
                    valores_linx.append(parse_valor_string(valor_db))
                    valores_honda.append(parse_valor_string(valor))
                    tipos_ajustes.append(tipo_ajuste)
                    origens.append('CNH' if origem == 1258 else 'Plano Legal')

        # --- Monta DataFrame com os dados compatíveis ---
        cabecalhos = ['TITULO', 'DUPLICATA', 'VALOR']
        cabecalhos_excel = ['TITULO', 'DUPLICATA', 'VALOR_LINX', 'VALOR_HONDA', 'TIPO DE AJUSTE', 'ORIGEM']
        data = {
            cabecalhos[0]: titulos,
            cabecalhos[1]: duplicatas,
            cabecalhos[2]: valores_linx
        }
        data_excel = {
            cabecalhos_excel[0]: titulos,
            cabecalhos_excel[1]: duplicatas,
            cabecalhos_excel[2]: valores_linx,
            cabecalhos_excel[3]: valores_honda,
            cabecalhos_excel[4]: tipos_ajustes,
            cabecalhos_excel[5]: origens,
        }
        df = pd.DataFrame(data, columns=cabecalhos)
        df_excel = pd.DataFrame(data_excel, columns=cabecalhos_excel)

        hoje = datetime.now().strftime("%d-%m-%Y")

        # Caminhos base usando Path (melhor que strings com \\)
        base_dir = P(r"\\172.17.67.14\findev$\Automação - CNH\Preparação das Baixas")
        csv_dir = base_dir / "Arquivos_csv"
        excel_dir = base_dir / "Arquivos_excel"

        # Monta os nomes de arquivos de forma segura e legível
        arquivo_csv = csv_dir / f"{nome_loja}_{hoje}.csv"
        arquivo_excel = excel_dir / f"{nome_loja}_{hoje}.xlsx"

        # Salva os arquivos
        df.to_csv(arquivo_csv, index=False, sep=';', encoding='utf-8-sig')
        df_excel.to_excel(arquivo_excel, index=False)

        return True, 'Automação de extração de dados do pdf concluída.'
    except Exception as e:
        return False, f'Erro ao verificar os dados da Linx.\nDescrição: {str(e)}'


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
    