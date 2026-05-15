# RAG Retrieval Filters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add document-level and quality-level retrieval filters to the RAG chat path.

**Architecture:** Chat requests accept an optional retrieval filter object and pass it into the orchestrator config. Retrieval uses quality controls for overfetching and vector score filtering. Evidence applies DB-backed document filters and rerank score filtering before synthesis.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, pytest, FAISS-backed vector search.

---

### Task 1: Add API Filter Contract

**Files:**
- Modify: `backend/app/api/chat.py`
- Modify: `backend/app/agents/orchestrator.py`
- Test: `backend/tests/integration/test_chat_flow.py`

- [ ] **Step 1: Write failing test**

Add a chat API test that sends `filters` in `/api/v1/chat/query/stream` and asserts `orchestrator.run()` receives them as `filters=...`.

- [ ] **Step 2: Run failing test**

Run: `pytest -q backend/tests/integration/test_chat_flow.py::test_streaming_chat_passes_retrieval_filters`
Expected: FAIL because `ChatRequest` does not expose filters and `orchestrator.run()` does not receive them.

- [ ] **Step 3: Implement API contract**

Add `RetrievalFilters` to `chat.py`, add `filters` to `ChatRequest`, and pass dumped filters into `orchestrator.run()`. Add `filters` to `Orchestrator.run()` and store them in `state["config"]["filters"]`.

- [ ] **Step 4: Verify**

Run: `pytest -q backend/tests/integration/test_chat_flow.py::test_streaming_chat_passes_retrieval_filters`
Expected: PASS.

### Task 2: Add Retrieval Quality Filters

**Files:**
- Modify: `backend/app/agents/retrieval.py`
- Test: `backend/tests/unit/test_retrieval_agent.py`

- [ ] **Step 1: Write failing test**

Add a test proving `overfetch_multiplier` changes FAISS `top_k` and `min_vector_score` filters low-scoring candidates.

- [ ] **Step 2: Run failing test**

Run: `pytest -q backend/tests/unit/test_retrieval_agent.py::test_retrieval_agent_applies_quality_filters`
Expected: FAIL because retrieval hard-codes `top_k * 2` and does not filter vector scores.

- [ ] **Step 3: Implement retrieval filtering**

Read filters from `state["config"]["filters"]`, clamp `overfetch_multiplier` to at least 1, search with `top_k * multiplier`, and keep candidates with score >= `min_vector_score`.

- [ ] **Step 4: Verify**

Run: `pytest -q backend/tests/unit/test_retrieval_agent.py::test_retrieval_agent_applies_quality_filters`
Expected: PASS.

### Task 3: Add Evidence Document Filters

**Files:**
- Modify: `backend/app/agents/evidence.py`
- Create: `backend/tests/unit/test_evidence_agent.py`

- [ ] **Step 1: Write failing tests**

Add tests proving `document_ids`, `status`, and `min_rerank_score` are applied before final chunks are returned.

- [ ] **Step 2: Run failing tests**

Run: `pytest -q backend/tests/unit/test_evidence_agent.py`
Expected: FAIL because evidence currently loads chunks by ID only and uses a fixed rerank threshold.

- [ ] **Step 3: Implement DB-backed filters**

Join `DocumentChunk.document`, apply requested document filters, then apply `min_rerank_score` after reranking.

- [ ] **Step 4: Verify**

Run: `pytest -q backend/tests/unit/test_evidence_agent.py`
Expected: PASS.

### Task 4: Regression Suite

**Files:**
- Verify all modified backend tests.

- [ ] **Step 1: Run targeted tests**

Run: `pytest -q backend/tests/unit/test_retrieval_agent.py backend/tests/unit/test_evidence_agent.py backend/tests/integration/test_chat_flow.py`
Expected: PASS.

- [ ] **Step 2: Run full backend suite**

Run from `backend`: `pytest -q`
Expected: PASS.
