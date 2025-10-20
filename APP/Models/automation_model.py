from .base_model import CoreModel
from .enums_model import AutomationType  # Lembra dos Enums que criamos?
from typing import Optional

class Automation(CoreModel):
    name: str        
    description: Optional[str] = None              
    script_path: str    
    type: AutomationType           
    schedule_cron: Optional[str] = None               
    ax_execution_time: int = 3600    
    created_by: str    
    department_id: str          