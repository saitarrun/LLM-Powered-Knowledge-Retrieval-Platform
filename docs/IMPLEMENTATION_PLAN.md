# Implementation Plan: Nexus RAG Platform (Complete)

**Status:** READY FOR IMPLEMENTATION  
**Timeline:** 4 days (Phase 1: 2 days, Phase 2: 2 days)  
**Difficulty:** Medium (scaffolding exists, integration work required)  
**Team Size:** 1-2 engineers  

---

## Overview

This plan wires the Nexus RAG platform's existing orchestrator and agents into a functional end-to-end system. The work is sequenced in two phases: validate the pipeline first (Phase 1), then secure it for team use (Phase 2).

**Why this approach:**
- Phase 1 endpoints are completely functional but unsafe (no auth, no approval gates)
- Separate phases allow testing with real data before adding complexity
- Minimal refactoring of existing code — mostly integration and new endpoints

**Dependencies:** All runtime dependencies already configured (Redis, Neo4j, FAISS, Celery). No new libraries needed.

---

## Milestones & Timeline

### Phase 1: Core Data Pipeline (Days 1-2)

**Milestone 1.1: Missing Agents (4 hours)**
- Implement RetrievalAgent (FAISS query wrapper)
- Implement CriticAgent (validation/hallucination detection)
- Both follow BaseAgent pattern from existing agents

**Milestone 1.2: Document Ingestion Pipeline (5 hours)**
- Rewrite POST `/api/v1/documents/upload` to ingest and index
- Wire text extraction (PDF, DOCX, TXT)
- Wire chunking and embedding generation
- Store chunks in database and FAISS index

**Milestone 1.3: Chat Endpoint with Orchestrator (6 hours)**
- Rewrite POST `/api/v1/chat/query/stream` to call orchestrator
- Implement SSE (Server-Sent Events) streaming
- Wire QueryLog persistence with latency tracking

**Milestone 1.4: Phase 1 Testing & Validation (3 hours)**
- Manual end-to-end test: upload → query → response
- Verify FAISS index grows
- Verify agent traces persist
- Document any issues for Phase 2

**Phase 1 Total: ~18 hours (fits in 2 days with breaks)**

### Phase 2: Security & Approval (Days 3-4)

**Milestone 2.1: Authentication Infrastructure (4 hours)**
- Implement JWT token generation and validation
- Add User model and role enum
- Wire auth middleware to FastAPI

**Milestone 2.2: Authorization & Permissions (3 hours)**
- Implement permission checks (viewer/curator/admin roles)
- Add permission decorators to routes
- Lock down document and approval endpoints

**Milestone 2.3: Approval Workflow Backend (4 hours)**
- Implement approval endpoints (GET pending, POST approve, POST reject)
- Add AuditLog model for tracking
- Wire status updates (pending → indexed or rejected)

**Milestone 2.4: Phase 2 Testing & Deployment (3 hours)**
- Test auth flows (register, login, token refresh)
- Test role-based access (viewer vs curator vs admin)
- Smoke test with team users
- Document any issues for production

**Phase 2 Total: ~14 hours (fits in 2 days with breaks)**

---

## File & Module Breakdown

### Backend Module Structure

```
backend/app/
├── agents/
│   ├── base.py              [EXISTING] BaseAgent class
│   ├── retrieval.py         [NEW] RetrievalAgent
│   ├── critic.py            [NEW] CriticAgent
│   ├── orchestrator.py       [EXISTING] Main pipeline
│   ├── evidence.py           [EXISTING]
│   ├── synthesis.py          [EXISTING]
│   ├── query_understanding.py [EXISTING]
│   └── ...
│
├── api/
│   ├── documents.py          [MODIFY] Implement ingestion
│   ├── chat.py               [MODIFY] Implement streaming
│   ├── settings.py           [EXISTING]
│   ├── auth.py               [NEW - Phase 2] Register, login, refresh
│   ├── users.py              [NEW - Phase 2] User management (admin)
│   └── approval.py           [NEW - Phase 2] Approval workflow
│
├── core/
│   ├── config.py             [EXISTING]
│   ├── auth.py               [NEW - Phase 2] JWT logic
│   ├── permissions.py        [NEW - Phase 2] Role checks
│   └── logging.py            [EXISTING]
│
├── db/
│   ├── models.py             [MODIFY] Add User, AuditLog; extend Document
│   ├── database.py           [EXISTING]
│   └── alembic/              [ADD - Phase 2] Migration for User/AuditLog tables
│
├── ingestion/
│   ├── pipeline.py           [NEW] Orchestrate chunking + embedding
│   ├── chunking/
│   │   └── chunker.py        [EXISTING]
│   ├── loaders/
│   │   └── parser.py         [EXISTING]
│   └── embeddings.py         [NEW or MODIFY] Embedding generation
│
├── services/
│   ├── llm_provider.py       [ENSURE EXISTS]
│   ├── embedding.py          [ENSURE EXISTS or CREATE]
│   ├── cache.py              [MODIFY - Phase 2] Use Redis for auth tokens
│   └── faiss_manager.py      [NEW] FAISS index lifecycle (save/load)
│
├── vectorstore/
│   ├── faiss_store.py        [EXISTING]
│   └── bm25_store.py         [EXISTING]
│
├── graph/
│   └── extractor.py          [EXISTING]
│
└── main.py                    [MODIFY] Add new routes, middleware

tests/
├── unit/
│   ├── test_retrieval_agent.py       [NEW - Phase 1]
│   ├── test_critic_agent.py          [NEW - Phase 1]
│   ├── test_document_ingestion.py    [NEW - Phase 1]
│   └── test_auth.py                  [NEW - Phase 2]
│
├── integration/
│   ├── test_chat_flow.py             [NEW - Phase 1]
│   ├── test_document_upload_flow.py  [NEW - Phase 1]
│   └── test_auth_flow.py             [NEW - Phase 2]
│
└── e2e/
    ├── test_full_pipeline.py         [NEW - Phase 1]
    └── test_approved_docs.py         [NEW - Phase 2]

```

---

## Data Model Changes

### Phase 1 Changes

**Modify: `Document` model**
```python
class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    filename = Column(String, index=True)
    content_type = Column(String)
    file_path = Column(String)
    
    # NEW fields
    approval_required = Column(Boolean, default=False)  # Require approval before indexing?
    status = Column(String, default="pending")  # pending, indexed, rejected, failed
    approved_by = Column(String, nullable=True)  # user_id who approved
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
    
    # NEW field
    embedding_id = Column(String, nullable=True)  # Reference to FAISS index position (or store as vector)
    indexed_at = Column(DateTime, nullable=True)
    
    document = relationship("Document", back_populates="chunks")
```

**Modify: `QueryLog` model**
```python
class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, nullable=True)  # Phase 2: link to user
    conversation_id = Column(String, nullable=True)  # Track conversation threads
    query = Column(String)
    rewritten_query = Column(String, nullable=True)
    answer = Column(Text, nullable=True)
    latency_ms = Column(Integer, default=0)
    token_count = Column(Integer, default=0)  # LLM tokens used
    
    # NEW field for storing full trace
    trace_json = Column(Text, nullable=True)  # Full orchestrator trace as JSON
    
    feedback = Column(Integer, nullable=True)  # 0=Down, 1=Up
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
```

### Phase 2 Changes

**New: `User` model**
```python
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="viewer")  # viewer, curator, admin
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    approved_documents = relationship("Document", foreign_keys=[Document.approved_by])
    audit_logs = relationship("AuditLog", back_populates="user")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    action = Column(String)  # "upload", "approve", "reject", "delete", "login"
    resource_type = Column(String)  # "document", "user"
    resource_id = Column(String)
    details = Column(Text, nullable=True)  # Extra context (error message, etc)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    user = relationship("User", back_populates="audit_logs")
```

### Database Migrations (Phase 2)

```bash
# Create migration files
alembic revision --autogenerate -m "Add User and AuditLog models"
alembic revision --autogenerate -m "Add approval fields to Document"
alembic revision --autogenerate -m "Add user_id and trace to QueryLog"

# Apply during Phase 2 deployment
alembic upgrade head
```

---

## API Routes

### Phase 1 Routes (No Auth)

**Documents Endpoint**
```
POST /api/v1/documents/upload
  Request:
    - file: UploadFile (PDF, DOCX, TXT)
    - approval_required: bool (optional, default False)
  Response:
    {
      "status": "processing",
      "doc_id": "uuid",
      "filename": "example.pdf",
      "message": "Document queued for ingestion"
    }
  Process:
    1. Save file to disk
    2. Extract text via parser.py
    3. Create Document record with status="processing"
    4. Chunk text via chunker.py
    5. Generate embeddings via embedding service
    6. Store chunks in database + FAISS index
    7. Update Document status → "indexed" (or "pending" if approval_required)
    8. Return success

GET /api/v1/documents
  Response:
    {
      "documents": [
        {
          "id": "uuid",
          "filename": "example.pdf",
          "status": "indexed",
          "chunk_count": 42,
          "indexed_at": "2026-04-23T12:00:00Z",
          "approval_required": false,
          "approved_by": null
        }
      ],
      "total": 1
    }

GET /api/v1/documents/{doc_id}
  Response:
    {
      "id": "uuid",
      "filename": "example.pdf",
      "status": "indexed",
      "chunks": 42,
      "created_at": "2026-04-23T11:50:00Z",
      "indexed_at": "2026-04-23T12:00:00Z"
    }

DELETE /api/v1/documents/{doc_id}
  Response: { "status": "deleted", "id": "uuid" }
  Process:
    1. Remove document record from database (cascade deletes chunks)
    2. Remove chunks from FAISS index
```

**Chat Endpoint (Streaming)**
```
POST /api/v1/chat/query/stream
  Request:
    {
      "query": "What does this document say about X?",
      "conversation_id": "uuid" (optional),
      "top_k": 5 (optional, default 5)
    }
  
  Response: Server-Sent Events (SSE)
    Yields events in order:
    1. trace events: {"type": "trace", "trace": {...orchestrator trace...}}
    2. token events: {"type": "token", "token": "the answer streaming"}
    3. citation events: {"type": "citations", "citations": [{...}]}
    4. final event: {"type": "done"}
  
  Process:
    1. Call orchestrator.run(query, top_k)
    2. Stream each event from orchestrator as SSE
    3. On synthesis completion, save QueryLog with latency

GET /api/v1/conversations
  Response:
    {
      "conversations": [
        {
          "id": "uuid",
          "query_count": 5,
          "created_at": "2026-04-23T11:00:00Z",
          "last_query_at": "2026-04-23T12:30:00Z"
        }
      ]
    }

GET /api/v1/conversations/{conversation_id}
  Response:
    {
      "id": "uuid",
      "messages": [
        {
          "role": "user",
          "content": "query",
          "timestamp": "2026-04-23T11:05:00Z"
        },
        {
          "role": "assistant",
          "content": "answer",
          "citations": [{...}],
          "latency_ms": 2450,
          "timestamp": "2026-04-23T11:05:05Z"
        }
      ]
    }
```

### Phase 2 Routes (With Auth)

**Authentication Endpoints**
```
POST /api/v1/auth/register
  Request:
    { "email": "user@example.com", "password": "..." }
  Response:
    { "user_id": "uuid", "email": "user@example.com", "role": "viewer" }

POST /api/v1/auth/login
  Request:
    { "email": "user@example.com", "password": "..." }
  Response:
    {
      "access_token": "jwt-token-here",
      "token_type": "Bearer",
      "expires_in": 3600
    }

POST /api/v1/auth/refresh
  Request (header):
    Authorization: Bearer {expired-token}
  Response:
    { "access_token": "new-jwt-token", "expires_in": 3600 }
```

**User Management (Admin Only)**
```
GET /api/v1/users
  Header: Authorization: Bearer {admin-token}
  Response:
    {
      "users": [
        {
          "id": "uuid",
          "email": "user@example.com",
          "role": "viewer",
          "created_at": "2026-04-23T10:00:00Z",
          "last_login": "2026-04-23T12:00:00Z"
        }
      ]
    }

POST /api/v1/users
  Header: Authorization: Bearer {admin-token}
  Request:
    { "email": "newuser@example.com", "password": "...", "role": "curator" }
  Response:
    { "user_id": "uuid", "email": "newuser@example.com", "role": "curator" }

PATCH /api/v1/users/{user_id}
  Header: Authorization: Bearer {self-or-admin-token}
  Request:
    { "role": "admin", "password": "..." }
  Response:
    { "user_id": "uuid", "email": "user@example.com", "role": "admin" }
```

**Approval Workflow**
```
GET /api/v1/documents/pending
  Header: Authorization: Bearer {curator-or-admin-token}
  Response:
    {
      "documents": [
        {
          "id": "uuid",
          "filename": "sensitive.pdf",
          "status": "pending",
          "uploaded_by": "user@example.com",
          "uploaded_at": "2026-04-23T11:50:00Z",
          "preview": "first 500 chars of content"
        }
      ]
    }

POST /api/v1/documents/{doc_id}/approve
  Header: Authorization: Bearer {curator-or-admin-token}
  Request: { }
  Response:
    {
      "status": "indexed",
      "id": "uuid",
      "approved_by": "approver@example.com",
      "approved_at": "2026-04-23T12:05:00Z"
    }
  Process:
    1. Verify document exists and status="pending"
    2. Generate embeddings if not already done
    3. Index chunks to FAISS
    4. Set status="indexed", approved_by, approved_at
    5. Create AuditLog entry
    6. Return success

POST /api/v1/documents/{doc_id}/reject
  Header: Authorization: Bearer {curator-or-admin-token}
  Request: { "reason": "Contains sensitive data" }
  Response:
    {
      "status": "rejected",
      "id": "uuid",
      "rejected_by": "approver@example.com",
      "rejected_at": "2026-04-23T12:05:00Z"
    }
  Process:
    1. Set status="rejected"
    2. Create AuditLog entry with reason
    3. Do NOT index to FAISS
    4. Return success
```

**Permission-Protected Versions of Phase 1 Endpoints (Phase 2)**

```
POST /api/v1/documents/upload
  Header: Authorization: Bearer {curator-or-admin-token}
  [Same as Phase 1, but permission-gated]

DELETE /api/v1/documents/{doc_id}
  Header: Authorization: Bearer {curator-or-admin-token}
  [Same as Phase 1, but permission-gated + audit log]

POST /api/v1/chat/query/stream
  Header: Authorization: Bearer {viewer-curator-or-admin-token}
  [Same as Phase 1, but permission-gated + user_id in QueryLog]
```

---

## Test Strategy

### Unit Tests (Phase 1)

**Test RetrievalAgent** (`tests/unit/test_retrieval_agent.py`)
```python
def test_retrieval_agent_searches_faiss():
    # Setup: Create mock document chunks in FAISS
    # Execute: Call RetrievalAgent with query
    # Assert: Returns top-k results ranked by similarity

def test_retrieval_agent_handles_empty_index():
    # Setup: Empty FAISS index
    # Execute: Call RetrievalAgent
    # Assert: Returns empty list, no error

def test_retrieval_agent_respects_top_k():
    # Setup: 20 chunks in index
    # Execute: Call with top_k=5
    # Assert: Returns exactly 5 results
```

**Test CriticAgent** (`tests/unit/test_critic_agent.py`)
```python
def test_critic_detects_hallucination():
    # Setup: State with answer that contradicts sources
    # Execute: Call CriticAgent
    # Assert: Flags hallucination with confidence score

def test_critic_passes_grounded_answer():
    # Setup: State with answer grounded in citations
    # Execute: Call CriticAgent
    # Assert: Passes validation

def test_critic_handles_no_citations():
    # Setup: State with answer but no citations
    # Execute: Call CriticAgent
    # Assert: Flags as risky, suggests user verify
```

**Test Document Ingestion** (`tests/unit/test_document_ingestion.py`)
```python
def test_chunk_text_splits_correctly():
    # Setup: Load sample PDF
    # Execute: Chunk via pipeline
    # Assert: Chunks are ~512 tokens each, overlap handled

def test_embedding_generation():
    # Setup: Sample chunks
    # Execute: Generate embeddings
    # Assert: Embeddings are 384-dim vectors (MiniLM model)

def test_faiss_index_stores_chunks():
    # Setup: Empty index
    # Execute: Add 100 chunks
    # Assert: Index has 100 vectors, can search

def test_document_record_created():
    # Setup: Upload document
    # Execute: Process ingestion
    # Assert: Document record in DB with status="processing" → "indexed"
```

### Integration Tests (Phase 1)

**Test Document Upload Flow** (`tests/integration/test_document_upload_flow.py`)
```python
def test_full_document_ingestion_flow():
    # Setup: Create test PDF
    # Execute: POST /api/v1/documents/upload
    # Assert: 
    #   - Returns status="processing"
    #   - Document created in DB
    #   - File saved to disk
    #   - Chunks created in DB
    #   - FAISS index has vectors
    #   - Status eventually becomes "indexed"

def test_upload_with_approval_required():
    # Setup: Create test PDF with approval_required=true
    # Execute: POST /api/v1/documents/upload
    # Assert: Document status="pending", not indexed to FAISS

def test_get_documents_lists_all():
    # Setup: Upload 5 documents
    # Execute: GET /api/v1/documents
    # Assert: Returns all 5 with correct metadata

def test_delete_document_removes_from_index():
    # Setup: Upload and index document
    # Execute: DELETE /api/v1/documents/{id}
    # Assert:
    #   - Document deleted from DB
    #   - Chunks deleted from DB
    #   - Vectors removed from FAISS
```

**Test Chat Flow** (`tests/integration/test_chat_flow.py`)
```python
def test_chat_streams_response():
    # Setup: Upload document, index it
    # Execute: POST /api/v1/chat/query/stream with question
    # Assert:
    #   - Stream contains trace events
    #   - Stream contains token events (answer)
    #   - Stream contains citation events
    #   - QueryLog created with latency

def test_chat_end_to_end():
    # Setup: Upload 3 documents
    # Execute: Query orchestrator → retrieval → reranking → synthesis
    # Assert:
    #   - Answer is coherent
    #   - Citations point to actual chunks
    #   - Traces show all agent steps
    #   - Latency is recorded

def test_chat_with_no_documents():
    # Setup: Empty knowledge base
    # Execute: POST /api/v1/chat/query/stream
    # Assert: Returns graceful error or "no documents found"
```

### Unit Tests (Phase 2)

**Test Auth** (`tests/unit/test_auth.py`)
```python
def test_jwt_token_generation():
    # Setup: Create user
    # Execute: Generate token
    # Assert: Token contains user_id and role, expires in 1 hour

def test_jwt_validation():
    # Setup: Valid token
    # Execute: Validate token
    # Assert: Extracts user_id and role correctly

def test_invalid_token_rejected():
    # Setup: Tampered token
    # Execute: Validate
    # Assert: Raises exception

def test_expired_token_rejected():
    # Setup: Expired token
    # Execute: Validate
    # Assert: Raises exception

def test_password_hashing():
    # Setup: Plain password
    # Execute: Hash via bcrypt
    # Assert: Hash is irreversible, same password produces same hash
```

**Test Permissions** (`tests/unit/test_permissions.py`)
```python
def test_viewer_can_query():
    # Setup: Viewer token
    # Execute: Check permission for /api/v1/chat/query/stream
    # Assert: Permission granted

def test_viewer_cannot_upload():
    # Setup: Viewer token
    # Execute: Check permission for /api/v1/documents/upload
    # Assert: Permission denied

def test_curator_can_approve():
    # Setup: Curator token
    # Execute: Check permission for /api/v1/documents/{id}/approve
    # Assert: Permission granted

def test_admin_can_manage_users():
    # Setup: Admin token
    # Execute: Check permission for /api/v1/users
    # Assert: Permission granted
```

### Integration Tests (Phase 2)

**Test Auth Flow** (`tests/integration/test_auth_flow.py`)
```python
def test_register_user():
    # Execute: POST /api/v1/auth/register
    # Assert: User created, can login

def test_login_returns_token():
    # Setup: Registered user
    # Execute: POST /api/v1/auth/login
    # Assert: Returns valid JWT token

def test_token_refresh():
    # Setup: Expired token
    # Execute: POST /api/v1/auth/refresh
    # Assert: Returns new valid token

def test_protected_endpoint_requires_auth():
    # Setup: Endpoint without token
    # Execute: GET /api/v1/documents
    # Assert: Returns 401 Unauthorized
```

**Test Approval Workflow** (`tests/integration/test_approval_flow.py`)
```python
def test_curator_approves_document():
    # Setup: Document pending approval, curator user
    # Execute: POST /api/v1/documents/{id}/approve
    # Assert:
    #   - Status becomes "indexed"
    #   - Chunks indexed to FAISS
    #   - AuditLog created

def test_curator_rejects_document():
    # Setup: Document pending approval
    # Execute: POST /api/v1/documents/{id}/reject
    # Assert:
    #   - Status becomes "rejected"
    #   - Chunks NOT indexed
    #   - AuditLog created with reason
    #   - Cannot query this document

def test_only_curator_can_approve():
    # Setup: Viewer user
    # Execute: POST /api/v1/documents/{id}/approve
    # Assert: Returns 403 Forbidden
```

### E2E Tests

**Full Pipeline** (`tests/e2e/test_full_pipeline.py`)
```python
def test_user_journey_phase_1():
    # 1. Upload document via POST /api/v1/documents/upload
    # 2. List documents via GET /api/v1/documents
    # 3. Query via POST /api/v1/chat/query/stream
    # 4. Verify answer has citations
    # Assert: End-to-end system works

def test_user_journey_phase_2():
    # 1. Register user via POST /api/v1/auth/register
    # 2. Login via POST /api/v1/auth/login
    # 3. Upload document with approval_required=true
    # 4. Admin approves via POST /api/v1/documents/{id}/approve
    # 5. User queries via POST /api/v1/chat/query/stream
    # Assert: Full secure flow works
```

### Test Coverage Goals

| Phase | Unit Coverage | Integration Coverage | E2E |
|-------|---------------|----------------------|-----|
| 1 | 90%+ (agents, ingestion) | 95%+ (upload, chat flows) | 2 happy paths |
| 2 | 85%+ (auth, permissions) | 90%+ (auth, approval, protected endpoints) | 2 happy paths |

---

## Deployment Checklist

### Phase 1 Deployment (Local/Staging)

**Pre-Deployment:**
- [ ] All Phase 1 unit tests passing (100% code coverage for new agents)
- [ ] All Phase 1 integration tests passing
- [ ] FAISS index builds without error on empty database
- [ ] Neo4j connection verified
- [ ] Redis connection verified
- [ ] All environment variables set (see `.env.example`)

**Database:**
- [ ] Run any new migrations (if schema changed)
  ```bash
  alembic upgrade head
  ```
- [ ] Verify Document and DocumentChunk tables have new columns

**Build & Run:**
- [ ] Build backend image: `docker build -f backend/Dockerfile -t nexus-backend:latest .`
- [ ] Start services: `docker-compose up`
- [ ] Health check: `curl http://localhost:8000/api/health`
- [ ] Frontend loads: `http://localhost:3000`

**Validation:**
- [ ] Upload test PDF via frontend chat page
  - Verify document appears in "Archive" page
  - Verify chunk count shows > 0
  - Verify status says "indexed"
- [ ] Query via frontend chat page
  - Type a question about the document
  - Verify streaming response with citations
  - Check browser console for no errors
- [ ] Verify FAISS index file exists: `ls -lh data/faiss_index`
- [ ] Verify QueryLog populated: `sqlite3 data/rag.db "SELECT COUNT(*) FROM query_logs"`

**Smoke Test Script:**
- [ ] Run provided smoke test: `./.github/scripts/smoke_test.py`
- [ ] All assertions pass

**Known Issues to Document:**
- [ ] None expected, note any issues found during validation

---

### Phase 2 Deployment (Team Environment)

**Pre-Deployment:**
- [ ] All Phase 2 unit tests passing
- [ ] All Phase 2 integration tests passing
- [ ] Phase 1 still working (regression tests pass)
- [ ] Auth middleware integrated without breaking Phase 1 endpoints

**Database Migrations:**
- [ ] Create migration: `alembic revision --autogenerate -m "Add User and AuditLog"`
- [ ] Review migration file for correctness
- [ ] Run migration: `alembic upgrade head`
- [ ] Verify User and AuditLog tables created
- [ ] Create initial admin user:
  ```bash
  python -c "
  from app.db.database import SessionLocal
  from app.db.models import User
  from app.core.auth import hash_password
  db = SessionLocal()
  admin = User(email='admin@example.com', hashed_password=hash_password('initial-password'), role='admin')
  db.add(admin)
  db.commit()
  print(f'Admin user created: {admin.id}')
  "
  ```

**Configuration:**
- [ ] Set `SECRET_KEY` in config (for JWT signing)
- [ ] Verify `DATABASE_URL` points to persistent database
- [ ] Verify `REDIS_URL` for token caching

**Build & Deployment:**
- [ ] Build new backend image: `docker build -f backend/Dockerfile -t nexus-backend:v2 .`
- [ ] Deploy to staging environment (use your deployment tool)
- [ ] Health check: `curl https://staging.example.com/api/health`

**User Onboarding:**
- [ ] Create test users:
  - Admin: can manage users and approve docs
  - Curator: can upload and approve docs
  - Viewer: can only query
- [ ] Test each role via API:
  ```bash
  # Login as viewer
  TOKEN=$(curl -X POST https://staging.example.com/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"viewer@example.com","password":"..."}' | jq -r .access_token)
  
  # Try to upload (should fail)
  curl -X POST https://staging.example.com/api/v1/documents/upload \
    -H "Authorization: Bearer $TOKEN" -F "file=@test.pdf"
  # Expected: 403 Forbidden
  ```

**Validation:**
- [ ] Register new user via API
- [ ] Login returns valid token
- [ ] Protected endpoints reject requests without token
- [ ] Viewer can query, cannot upload
- [ ] Curator can upload and approve
- [ ] Admin can manage users
- [ ] Upload with `approval_required=true` → pending status
- [ ] Curator approves → indexed status
- [ ] AuditLog tracks all actions

**Slack Integration (Optional):**
- [ ] Configure Slack webhook URL in environment
- [ ] When document uploaded with `approval_required=true`, Slack message sent to `#approvals`
- [ ] Curator clicks "Approve" button in Slack → POST to `/documents/{id}/approve`
- [ ] Approval recorded and AuditLog updated

---

### Production Deployment

**Pre-Deployment Checklist:**
- [ ] Load test with 10+ concurrent users (basic load test)
- [ ] Verify FAISS index performance with 1000+ chunks
- [ ] Verify query latency < 5 seconds (P95)
- [ ] Verify token refresh rate under load
- [ ] All tests pass in CI/CD pipeline
- [ ] Code review approved
- [ ] Security review completed (auth, input validation)
- [ ] Documentation updated (API docs, user guide)

**Database:**
- [ ] Backup production database before migration
- [ ] Run migrations in transaction
- [ ] Verify rollback plan if migration fails

**Secrets Management:**
- [ ] `SECRET_KEY` rotated and secured
- [ ] `OPENAI_API_KEY` secured in secrets manager
- [ ] Database credentials not in code
- [ ] Use environment variables or secrets manager

**Deployment:**
- [ ] Deploy to production (blue-green or canary)
- [ ] Monitor error rates (target: < 0.1% 5xx errors)
- [ ] Monitor latency (target: P50 < 2s, P95 < 5s, P99 < 10s)
- [ ] Monitor LLM token usage and costs

**Post-Deployment:**
- [ ] Health checks passing
- [ ] No error spikes in logs
- [ ] Sample queries working correctly
- [ ] Slack approval workflow tested
- [ ] Team can login and use system
- [ ] Document approvals working end-to-end

**Rollback Plan:**
- [ ] If critical error: revert to previous image
- [ ] Database migration rollback: `alembic downgrade -1`
- [ ] Notify team of incident
- [ ] Root cause analysis post-incident

---

## Risk Assessment & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| FAISS index corrupts | System down | Low | Backup index daily, test recovery process |
| Embedding generation fails | Ingestion stops | Medium | Add retry logic, fallback to BM25 |
| JWT token expiration not handled | Auth breaks | Medium | Implement automatic refresh before expiry |
| Concurrent approvals conflict | Data corruption | Low | Use database-level locking or Celery task queue |
| N+1 queries during chat | Slow responses | Medium | Use SQLAlchemy eager loading, verify with query logs |
| Password hashing too slow | Slow registration | Low | Use bcrypt with proper rounds (12-14) |
| CORS misconfiguration | Frontend blocked | Low | Verify CORS config for frontend domains |

---

## Success Metrics

### Phase 1 Success
- [ ] End-to-end flow works: upload → query → answer
- [ ] FAISS index performance: < 100ms search for 1000+ chunks
- [ ] Streaming response latency: < 3 seconds first token
- [ ] All tests passing (90%+ coverage)
- [ ] Zero regressions from design doc

### Phase 2 Success
- [ ] All auth flows working (register, login, refresh)
- [ ] Role-based access enforced correctly
- [ ] Approval workflow complete (pending → indexed)
- [ ] Audit trail captures all actions
- [ ] Team can login and use system
- [ ] Zero security vulnerabilities (manual review)

---

## Appendix: Command Reference

**Local Development**
```bash
# Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Run backend
python -m uvicorn app.main:app --reload

# Run frontend
npm run dev

# Run tests
pytest tests/ -v --cov=app --cov-report=html

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "Description"

# Docker
docker-compose up --build
docker-compose down
docker-compose exec backend bash  # Shell into container
```

**Deployment**
```bash
# Build images
docker build -f backend/Dockerfile -t nexus-backend:latest .
docker build -f frontend/Dockerfile -t nexus-frontend:latest .

# Push to registry
docker push nexus-backend:latest
docker push nexus-frontend:latest

# Deploy to cloud (example: fly.io)
flyctl deploy --config fly.toml
```

