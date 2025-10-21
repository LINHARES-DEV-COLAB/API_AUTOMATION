from dataclasses import dataclass 

@dataclass
class User:
    """
    Representa um usuário do sistema, contendo as credenciais e o nome da loja.

    Atributos:
        codigo (str): Código da empresa/revenda.
        usuario (str): Nome de usuário para login.
        senha (str): Senha associada ao usuário.
        nome_loja (str): Nome da loja correspondente ao usuário.
    """
    codigo: str
    usuario: str
    senha: str
    nome_loja:str