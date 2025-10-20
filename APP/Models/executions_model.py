from APP.Models.automation_model import Automation
from APP.Models.enums_model import AutomationType
from .base_model import CoreModel
from .enums_model import Status  # Lembra do enum Status?
from typing import Optional
from datetime import date, datetime

class Execution(CoreModel):
    automation_id: str 
    triggered_by: Optional[str] = None     
    status: Status.pending              
    start_time: Optional[datetime] = None      
    end_time: Optional[datetime] = None
    exit_code: Optional[int] = None        
    output_log: Optional[str] = None          
    error_log: Optional[str] = None