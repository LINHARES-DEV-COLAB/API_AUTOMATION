# ExcelIntegration.py
import pandas as pd
from pathlib import Path
from APP.DTO.FIDC_DTO import LoginDTO
from APP.Config.fidc_site_estrutura import Paths as config
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from collections import OrderedDict

XLSX_PATH = r"C:\Users\sousa.lima\Documents\Projetos\EmissaoBoletoFIDC\FIDC CAP DIARIO.xlsx"


def load_login_from_excel(sheet: str = "Para pagamento -->") -> LoginDTO:
    """Lê o usuário da célula K6 e a senha da célula L6 da planilha."""

    if not XLSX_PATH.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {XLSX_PATH}")

    # ✅ Lê apenas as colunas K e L (10 e 11)
    df = pd.read_excel(XLSX_PATH, sheet_name=sheet, usecols="K:L")

    # ✅ Linha 6 (índice 5), coluna 0 = K6 → usuário
    usuario = str(df.iat[4, 0]).strip()

    # ✅ Linha 6 (índice 5), coluna 1 = L6 → senha
    senha = str(df.iat[4, 1]).strip()

    if not usuario or not senha:
        raise ValueError("Usuário ou senha não encontrados nas células K6 e L6.")

    return LoginDTO(
        usuario=usuario,
        senha=senha
    )

# app/logic/ConsultaFIDC.py


@dataclass(frozen=True)
class ConsultaFIDC:
    emp: str
    nota_fiscal: str

def _normalize_cell(v) -> str:
    if pd.isna(v):
        return ""
    s = str(v).strip()
    # Se vier float "123.0", converte para "123"
    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
    except:
        pass
    return s

def _find_sheet_case_insensitive(xlsx: Path, desired: str) -> str:
    xl = pd.ExcelFile(xlsx)
    for name in xl.sheet_names:
        if name.strip().lower() == desired.strip().lower():
            return name
    raise ValueError(f"Aba '{desired}' não encontrada. Abas disponíveis: {xl.sheet_names}")

def _pick_col(df: pd.DataFrame, candidates: list[str]) -> str:
    cols_map = {c.lower().strip(): c for c in df.columns}
    for key in candidates:
        if key in cols_map:
            return cols_map[key]
    raise ValueError(f"Não encontrei nenhuma destas colunas: {candidates}.\nEncontradas: {list(df.columns)}")

def selecionar_emp_e_primeira_nf(
    xlsx_path: str | Path,
    sheet_name: str = "FIDC Contas a pagar."
) -> ConsultaFIDC:
    xlsx = Path(xlsx_path)
    if not xlsx.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {xlsx}")

    # Localiza a aba sem depender de acentuação/caixa
    real_sheet = _find_sheet_case_insensitive(xlsx, sheet_name)

    # Lê só as colunas necessárias (se souber os nomes). Caso contrário, lê tudo.
    df = pd.read_excel(xlsx, sheet_name=real_sheet, engine="openpyxl")

    # Normaliza colunas (para matching)
    df.columns = [str(c).strip() for c in df.columns]

    # Encontra colunas de interesse
    emp_col = _pick_col(df, ["emp"])  # EMP exato
    nf_col = _pick_col(
        df,
        [
            "nota fiscal",
            "nº nota fiscal",
            "numero nota fiscal",
            "número nota fiscal",
            "nf",
            "nfe",
            "nf-e",
        ],
    )

    # Seleciona a primeira opção não nula de EMP (na ordem em que aparece)
    serie_emp = df[emp_col].astype(object).map(_normalize_cell)
    primeira_opcao_emp = next((v for v in serie_emp if v), None)
    if not primeira_opcao_emp:
        raise ValueError("Não encontrei um valor válido na coluna EMP.")

    # Filtra pelo EMP escolhido
    filtrado = df[serie_emp == primeira_opcao_emp].copy()
    if filtrado.empty:
        raise ValueError(f"Nenhuma linha encontrada para EMP='{primeira_opcao_emp}'.")

    # Pega a primeira linha filtrada e extrai a Nota Fiscal
    primeira_nf = _normalize_cell(filtrado.iloc[0][nf_col])
    if not primeira_nf:
        raise ValueError(f"'Nota Fiscal' vazia para EMP='{primeira_opcao_emp}' na primeira linha filtrada.")

    return ConsultaFIDC(emp=primeira_opcao_emp, nota_fiscal=primeira_nf)

def _norm(v) -> str:
    if pd.isna(v): return ""
    s = str(v).strip()
    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
    except:  # não é número
        pass
    return s

def notas_fiscais_do_emp(xlsx_path: str | Path,
                         sheet_name: str = "FIDC Contas a pagar.",
                         emp_escolhido: str = "") -> list[str]:
    x = Path(xlsx_path)
    if not x.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {x}")
    df = pd.read_excel(x, sheet_name=sheet_name, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]

    # localizar colunas
    emp_col = next((c for c in df.columns if c.lower() == "emp"), None)
    nf_col  = next((c for c in df.columns if c.lower() in
                   ["nota fiscal","nº nota fiscal","numero nota fiscal","número nota fiscal","nf","nfe","nf-e"]), None)
    if not emp_col or not nf_col:
        raise ValueError("Colunas 'EMP' e/ou 'Nota Fiscal' não encontradas.")

    # filtrar pelo EMP escolhido
    serie_emp = df[emp_col].astype(object).map(_norm)
    filtrado = df[serie_emp == emp_escolhido].copy()
    if filtrado.empty:
        return []

    # coletar NFs normalizadas (sem duplicatas, na ordem)
    nfs = []
    for v in filtrado[nf_col].tolist():
        nv = _norm(v)
        if nv and nv not in nfs:
            nfs.append(nv)
    return nfs

def _norm(v) -> str:
    if pd.isna(v): return ""
    s = str(v).strip()
    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
    except:
        pass
    return s

def carregar_dataframe(xlsx_path: str | Path, sheet_name: str) -> pd.DataFrame:
    x = Path(xlsx_path)
    if not x.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {x}")
    df = pd.read_excel(x, sheet_name=sheet_name)
    df.columns = [str(c).strip() for c in df.columns]
    return df

# No seu fidc_excel_integration.py
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# APP/Core/fidc_excel_integration.py

def mapear_emps_para_nfs(caminho_arquivo, sheet_name):
    """
    Mapeia empresas para NFs a partir de um arquivo Excel
    """
    try:
        logger.info(f"📖 Lendo arquivo Excel: {caminho_arquivo}")
        logger.info(f"📋 Planilha: {sheet_name}")
        
        df = pd.read_excel(caminho_arquivo, sheet_name=sheet_name)
        logger.info(f"✅ Excel carregado. Colunas: {list(df.columns)}")
        logger.info(f"📊 Total de linhas: {len(df)}")
        
        # ⭐ DEBUG: Mostra as primeiras linhas para ver os dados
        logger.info("🔍 Primeiras 5 linhas do DataFrame:")
        for i in range(min(5, len(df))):
            logger.info(f"   Linha {i}: {dict(df.iloc[i])}")
        
        # ⭐ CORREÇÃO: Verifica nomes alternativos para as colunas
        coluna_empresa = None
        coluna_nf = None
        
        # Procura a coluna de empresa
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if col_lower in ['empresa', 'emp', 'loja', 'revenda']:
                coluna_empresa = col
                break
        
        # Procura a coluna de nota fiscal
        for col in df.columns:
            col_lower = str(col).lower().strip()
            if any(x in col_lower for x in ['nota fiscal', 'nota', 'nf', 'nfe']):
                coluna_nf = col
                break
        
        if not coluna_empresa or not coluna_nf:
            logger.error(f"❌ Colunas não encontradas. Empresa: {coluna_empresa}, NF: {coluna_nf}")
            logger.error(f"❌ Colunas disponíveis: {list(df.columns)}")
            raise ValueError("Colunas 'Empresa' e 'Nota Fiscal' não encontradas")
        
        logger.info(f"✅ Usando coluna Empresa: '{coluna_empresa}'")
        logger.info(f"✅ Usando coluna Nota Fiscal: '{coluna_nf}'")
        
        # Limpa dados
        df = df.dropna(subset=[coluna_empresa, coluna_nf])
        df[coluna_empresa] = df[coluna_empresa].astype(str).str.strip()
        df[coluna_nf] = df[coluna_nf].astype(str).str.strip()
        
        # ⭐ DEBUG: Mostra valores únicos de empresas
        empresas_unicas = df[coluna_empresa].unique()
        logger.info(f"🏪 Empresas encontradas no Excel: {list(empresas_unicas)}")
        
        # Agrupa NFs por empresa
        mapa = df.groupby(coluna_empresa)[coluna_nf].apply(list).to_dict()
        
        logger.info(f"📈 Mapeamento concluído: {len(mapa)} empresas encontradas")
        for emp, nfs in mapa.items():
            logger.info(f"   {emp}: {len(nfs)} NFs - Primeiras 3: {nfs[:3]}")
        
        return mapa
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar Excel: {e}")
        raise