from dataclasses import dataclass

@dataclass(frozen=True)
class LoginDTO:
    usuario: str
    senha: str

    def masked(self) -> str:
        tail = self.senha[-2:] if self.senha else ""
        return f"LoginDTO(usuario={self.usuario}, senha=***{tail})"