from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentUpload(BaseModel):
    filename: str
    status: str
    message: Optional[str] = None
    timestamp: datetime