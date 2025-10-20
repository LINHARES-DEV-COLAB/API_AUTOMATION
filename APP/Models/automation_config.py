from sqlalchemy import false
from .base_model import CoreModel
from .enums_model import Config_Type  # Seu enum para config_type
from typing import Optional

class AutomationConfig(CoreModel): 
    automation_id: str 
    config_key: str
    config_value: Optional[str] = None         
    config_type:  Config_Type.string          
    is_secret: bool = false