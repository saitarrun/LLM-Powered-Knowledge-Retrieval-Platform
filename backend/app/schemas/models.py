from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class TraceEvent(BaseModel):
    agent: str
    action: str
    result: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Citation(BaseModel):
    id: Optional[str] = None
    document_name: str = "Source unavailable"
    chunk_text: str = ""
    chunk_id: Optional[str] = None
    document_id: Optional[str] = None
    snippet: str = ""
    available: bool = False
