import uuid
import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    filename = Column(String, index=True)
    content_type = Column(String)
    file_path = Column(String)
    status = Column(String, default="processing") # processing, indexed, failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    document_id = Column(String, ForeignKey("documents.id"))
    text = Column(Text)
    page_number = Column(Integer, nullable=True)
    chunk_index = Column(Integer)
    token_count = Column(Integer, default=0)
    
    document = relationship("Document", back_populates="chunks")

class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    query = Column(String)
    rewritten_query = Column(String, nullable=True)
    answer = Column(Text, nullable=True)
    latency_ms = Column(Integer, default=0)
    feedback = Column(Integer, nullable=True) # 0=Down, 1=Up
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    query_log_id = Column(String, ForeignKey("query_logs.id"))
    agent_name = Column(String)
    action = Column(String)
    result_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
