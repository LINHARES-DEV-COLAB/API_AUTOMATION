from .base_model import CoreModel
from typing import Optional

class Department(CoreModel):  
    name: str 
    code: str 
    description: Optional[str] = None 