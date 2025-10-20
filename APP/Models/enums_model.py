from enum import Enum
from sched import scheduler

class AutomationType(str, Enum):
    manual = "manual"
    scheduled = "scheduled"    
    triggered = "triggered"   

class Status(str, Enum):
    pending = "pending"
    running = "running"
    success = "success"  
    failed = "failed" 
    cancelled = "cancelled"

class Config_Type(str, Enum):
    string = "string"
    number = "number"
    boolean = "boolean"      
    json = "json"  
