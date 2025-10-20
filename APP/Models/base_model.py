from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CoreModel(BaseModel):
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True