from datetime import datetime

from pydantic import BaseModel, Field


class TraceEvent(BaseModel):
    agent: str
    action: str
    result: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Citation(BaseModel):
    id: str | None = None
    document_name: str = "Source unavailable"
    chunk_text: str = ""
    chunk_id: str | None = None
    document_id: str | None = None
    snippet: str = ""
    available: bool = False
