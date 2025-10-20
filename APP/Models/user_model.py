from sqlalchemy import false
from .base_model import CoreModel
from typing import Optional

class User(CoreModel):
    email: str  
    username: str
    hashed_password: str
    is_superuser: bool  = false
    department_id: Optional[str] = None   
