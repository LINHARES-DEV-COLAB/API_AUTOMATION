import os
from typing import Optional, Tuple
from ldap3 import Server, Connection, ALL, SUBTREE, Tls
from dotenv import load_dotenv

load_dotenv()

LDAP_HOST = os.getenv("LDAP_HOST", "localhost")
LDAP_PORT = int(os.getenv("LDAP_PORT", "389"))
LDAP_USE_SSL = os.getenv("LDAP_USE_SSL", "false").lower() == "true"
LDAP_DOMAIN = os.getenv("LDAP_DOMAIN", "")
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "")
ALLOWED_USERS = {u.strip().lower() for u in os.getenv("LDAP_ALLOWED_USERS", "").split(",") if u.strip()}

def usuario_autorizado(usuario: str) -> bool:
    if not ALLOWED_USERS:
        return True
    return usuario.lower() in ALLOWED_USERS

def _server() -> Server:
    # Se precisar validar CA, configure Tls(ca_certs_file="...") aqui
    return Server(LDAP_HOST, port=LDAP_PORT, use_ssl=LDAP_USE_SSL, get_info=ALL)

def autenticar_upn(usuario: str, senha: str) -> Tuple[bool, Optional[str]]:
    """
    Autentica no AD usando UPN (usuario@DOMINIO).
    Retorna (ok, erro) — erro = None se ok=True.
    """
    if not usuario_autorizado(usuario):
        return False, "Usuário sem permissão de acesso (lista de autorizados)."

    if not usuario or not senha:
        return False, "Usuário e senha são obrigatórios."

    upn = f"{usuario}@{LDAP_DOMAIN}" if LDAP_DOMAIN and "@" not in usuario else usuario
    try:
        conn = Connection(_server(), user=upn, password=senha, authentication="SIMPLE", auto_bind=True)
        conn.unbind()
        return True, None
    except Exception as e:
        return False, f"Falha na autenticação LDAP: {repr(e)}"

def buscar_atributos(usuario: str, senha: str, atributos=None) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    Exemplo extra: após autenticar, busca atributos do usuário no AD (via bind do próprio usuário).
    """
    upn = f"{usuario}@{LDAP_DOMAIN}" if LDAP_DOMAIN and "@" not in usuario else usuario
    try:
        conn = Connection(_server(), user=upn, password=senha, authentication="SIMPLE", auto_bind=True)
        # Em AD, geralmente userPrincipalName = UPN; podemos localizar a entrada pelo próprio bind DN:
        # Alternativa: pesquisar por sAMAccountName=usuario ou userPrincipalName=upn
        filtros = f"(|(userPrincipalName={upn})(sAMAccountName={usuario}))"
        conn.search(search_base=LDAP_BASE_DN, search_filter=filtros, search_scope=SUBTREE,
                    attributes=atributos or ["cn", "mail", "memberOf", "userPrincipalName", "department","description"])
        if not conn.entries:
            conn.unbind()
            return False, None, "Usuário autenticou, mas entrada não foi localizada no diretório."
        entry = conn.entries[0]
        data = {attr: entry[attr].value for attr in entry.entry_attributes}
        conn.unbind()
        return True, data, None
    except Exception as e:
        return False, None, f"Erro ao buscar atributos: {repr(e)}"
