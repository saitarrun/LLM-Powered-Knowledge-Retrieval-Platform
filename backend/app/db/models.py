import uuid
import datetime
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.database import Base


class UserRole(str, Enum):
    VIEWER = "viewer"
    CURATOR = "curator"
    ADMIN = "admin"

def generate_uuid():
    return str(uuid.uuid4())

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    filename = Column(String, index=True)
    content_type = Column(String)
    file_path = Column(String)
    status = Column(String, default="processing") # processing, indexed, failed, pending, rejected
    approval_required = Column(Boolean, default=False)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    indexed_at = Column(DateTime, nullable=True)
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
    embedding_id = Column(String, nullable=True)
    indexed_at = Column(DateTime, nullable=True)

    document = relationship("Document", back_populates="chunks")

class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    conversation_id = Column(String, nullable=True)
    query = Column(String)
    rewritten_query = Column(String, nullable=True)
    answer = Column(Text, nullable=True)
    latency_ms = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    trace_json = Column(Text, nullable=True)
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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String)  # upload, approve, reject, delete, login
    resource_type = Column(String, nullable=True)  # document, user
    resource_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
