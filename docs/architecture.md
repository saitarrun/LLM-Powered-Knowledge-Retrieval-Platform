# Nexus Architecture

## System Overview

Nexus is a **multi-agent RAG (Retrieval-Augmented Generation) platform** that combines advanced AI reasoning with reliable document retrieval. The system uses specialized agents, knowledge graphs, and vector search to provide accurate, cited answers.

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                           │
│                    (Next.js Frontend)                        │
└─────────────────┬───────────────────────────────────────────┘
                  │ REST API
┌─────────────────▼───────────────────────────────────────────┐
│                  API GATEWAY                                 │
│               (FastAPI Backend)                              │
└─┬───────────────┬──────────────────┬──────────────┬─────────┘
  │               │                  │              │
  ▼               ▼                  ▼              ▼
┌────────┐  ┌──────────┐      ┌──────────┐   ┌──────────┐
│ Chat   │  │Documents │      │ Settings │   │ Status   │
│Engine  │  │Management│      │Endpoint  │   │Check     │
└────────┘  └──────────┘      └──────────┘   └──────────┘
  │               │
  ▼               ▼
┌─────────────────────────────┐
│    AGENT ORCHESTRATION      │
│ (Orion, Critic, Synthesis)  │
└──┬──────────────────────┬───┘
   │                      │
   ▼                      ▼
┌──────────────┐  ┌────────────────────┐
│ Vector Store │  │  Knowledge Graph   │
│   (FAISS)    │  │     (Neo4j)        │
└──────────────┘  └────────────────────┘
   │                      │
   └──────────┬───────────┘
              ▼
        ┌──────────────┐
        │ Source Cache │
        │  (SQLite)    │
        └──────────────┘
```

## 🏗️ Core Components

### 1. Frontend (Next.js)
**Location:** `frontend/`

Responsibilities:
- Chat interface for user queries
- Document upload and management
- Real-time updates
- Responsive design with Tailwind CSS

Key files:
```
frontend/src/app/
├── page.tsx          # Home/hero section
├── chat/             # Chat conversation interface
├── documents/        # Document library
└── components/       # Reusable UI components
```

**Tech Stack:**
- Next.js 16 (App Router)
- React 19
- TypeScript
- Tailwind CSS
- Lucide icons
- Framer Motion

### 2. Backend API (FastAPI)
**Location:** `backend/`

Responsibilities:
- Handle API requests
- Coordinate agent execution
- Manage documents and chunks
- Expose vector search

Key files:
```
backend/app/
├── main.py              # App initialization
├── api/                 # Route handlers
│   ├── chat.py         # Chat endpoints
│   ├── documents.py    # Document CRUD
│   └── settings.py     # Config endpoints
├── agents/             # AI agents
│   ├── orion.py       # Planning agent
│   ├── critic.py      # Verification agent
│   └── synthesis.py   # Response synthesis
├── services/           # Business logic
│   ├── vector_store.py # FAISS wrapper
│   ├── llm.py         # OpenAI integration
│   └── graph.py       # Neo4j operations
├── core/              # Config & logging
└── db/                # Database models
```

**API Structure:**
```
/api/v1/
├── /documents
│   ├── GET  /              # List documents
│   ├── POST /upload        # Upload document
│   ├── GET  /{id}          # Get document
│   └── DELETE /{id}        # Delete document
├── /chat
│   ├── POST /              # Send message
│   └── GET  /{id}          # Get conversation
└── /settings
    ├── GET  /              # Get settings
    └── POST /              # Update settings
```

### 3. Vector Store (FAISS)
**Purpose:** Fast semantic search across document chunks

```python
# Workflow:
1. Document uploaded
2. Split into chunks (1000 chars, 200 overlap)
3. Generate embeddings (all-MiniLM-L6-v2)
4. Store in FAISS index
5. Query: embed user question → find similar chunks
```

**Features:**
- In-memory index (restart loses data)
- L2 distance metric
- Fast, accurate semantic search
- Future: pgvector for persistence

### 4. Knowledge Graph (Neo4j)
**Purpose:** Capture relationships between concepts and documents

```cypher
# Example structure:
(Document) -[:CONTAINS]-> (Chunk)
(Chunk) -[:MENTIONS]-> (Entity)
(Entity) -[:RELATED_TO]-> (Entity)
(Chunk) -[:SIMILAR_TO]-> (Chunk)
```

**Benefits:**
- Higher-order reasoning
- Explicit relationships
- Graph traversal for discovery
- Visualization capability

### 5. Agent System

**Orion (Planning Agent)**
- Analyzes user query
- Breaks into sub-tasks
- Routes to appropriate tools

**Critic (Verification Agent)**
- Evaluates retrieved documents
- Checks factual accuracy
- Validates citations

**Synthesis Agent**
- Combines findings
- Generates final response
- Ensures proper formatting

**Execution Flow:**
```
User Query
    ↓
Orion (Planning)
    ↓
Vector Search (FAISS)
Graph Query (Neo4j)
    ↓
Critic (Verification)
    ↓
LLM (OpenAI)
    ↓
Synthesis
    ↓
User Response
```

### 6. Task Queue (Celery + Redis)
**Purpose:** Async document processing

```python
# Example:
1. User uploads document
2. Task queued (fast response)
3. Worker processes async:
   - Parse document
   - Generate embeddings
   - Index in FAISS
   - Create graph nodes
4. User notified when complete
```

### 7. Workflow Engine (n8n)
**Purpose:** No-code automation and integrations

**Example workflows:**
- Scheduled document refresh
- Slack notification on new documents
- Calendar-triggered updates
- Custom data source connectors

## 🔄 Data Flow

### Document Ingestion
```
1. User uploads file
2. FastAPI /upload endpoint receives
3. Parse document (pdf, txt, docx)
4. Split into chunks
5. Generate embeddings
6. Store in FAISS
7. Create graph nodes
8. Save metadata to SQLite
9. Return success
```

### Query Processing
```
1. User sends question
2. Orion agent analyzes
3. Generate query embedding
4. FAISS similarity search → top K chunks
5. Neo4j graph traversal → related entities
6. Critic evaluates relevance
7. LLM generates response
8. Synthesis formats output
9. Return with citations
```

## 🗄️ Database Schema

### SQLite (Metadata)
```sql
documents
├── id (PK)
├── name
├── uploaded_at
├── size
└── status

chunks
├── id (PK)
├── document_id (FK)
├── content
├── embedding_id
└── created_at

conversations
├── id (PK)
├── user_id
├── created_at
└── status

messages
├── id (PK)
├── conversation_id (FK)
├── content
├── role (user/assistant)
└── metadata
```

### Neo4j (Knowledge Graph)
```
Node types:
- Document
- Chunk
- Entity
- Topic
- Concept

Relationship types:
- CONTAINS (Doc → Chunk)
- MENTIONS (Chunk → Entity)
- RELATED_TO (Entity → Entity)
- SIMILAR_TO (Chunk → Chunk)
- CLASSIFIED_AS (Entity → Topic)
```

### FAISS (Vector Index)
```
Index type: Flat (exhaustive search)
Dimension: 384 (all-MiniLM-L6-v2)
Metric: L2 (Euclidean distance)
Entries: One per chunk
```

## 🔐 Security Considerations

### Current State
- No authentication (development)
- Open CORS (localhost only)
- API keys in environment variables

### Production Roadmap
- [ ] JWT authentication
- [ ] OAuth2 integration
- [ ] API key management
- [ ] Row-level security (RLS) in database
- [ ] Encrypted sensitive data
- [ ] Rate limiting
- [ ] Input validation

## 📈 Scalability Path

### Phase 1 (Current)
- Single instance
- FAISS in-memory
- SQLite database
- Synchronous processing

### Phase 2 (Next)
- PostgreSQL + pgvector
- Distributed task queue
- Horizontal scaling
- Caching layer

### Phase 3 (Future)
- Multi-region deployment
- Sharded vector index
- Custom model fine-tuning
- Advanced observability

## 🧪 Testing Strategy

### Backend
```
├── Unit Tests
│   ├── Vector store operations
│   ├── Graph queries
│   └── LLM interactions
├── Integration Tests
│   ├── Document upload end-to-end
│   ├── Chat flow
│   └── API endpoints
└── Smoke Tests (CI/CD)
    └── Services healthy?
```

### Frontend
```
├── Component Tests (Vitest)
├── E2E Tests (Playwright)
└── Visual Regression Tests
```

## 🔍 Observability

### Current
- Stdout logging
- Docker logs
- Health check endpoint

### Future
- [ ] Structured logging (JSON)
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Distributed tracing
- [ ] Error tracking (Sentry)

## 📚 Related Docs
- [Contributing Guide](../CONTRIBUTING.md)
- [API Reference](./api.md) (coming soon)
- [Deployment Guide](./deployment.md) (coming soon)
- [Development Tips](./development.md) (coming soon)
