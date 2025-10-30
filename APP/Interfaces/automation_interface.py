from abc import ABC, abstractmethod

class automation_command(ABC):
    @abstractmethod
    def validate_parameters(self, params: dict) -> bool:
        pass
    
    @abstractmethod
    def execute(self, params: dict) -> dict:  # ← DEVE retornar dict
        pass