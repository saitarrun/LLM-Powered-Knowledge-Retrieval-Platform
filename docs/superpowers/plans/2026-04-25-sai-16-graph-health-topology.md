# SAI-16 Graph Health Topology Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let admins inspect knowledge graph topology and health from the graph page.

**Architecture:** Extend the existing document graph endpoint to return typed topology data and sanitized health metadata. Keep graph extraction/Neo4j access behind `GraphExtractor`, and render graph status states in the existing Next.js graph page. Add smoke tests around backend availability and small frontend helper tests around status classification.

**Tech Stack:** FastAPI, SQLAlchemy, Neo4j async driver, Next.js, react-force-graph-2d, Node test runner, pytest.

---

### Task 1: Backend Graph Health Contract

**Files:**
- Modify: `backend/app/graph/extractor.py`
- Modify: `backend/app/api/documents.py`
- Test: `backend/tests/integration/test_graph_endpoint.py`

- [ ] Write smoke tests for `/api/v1/documents/graph` returning `nodes`, `links`, and `health`.
- [ ] Verify tests fail because the endpoint is absent or incomplete.
- [ ] Add sanitized health/topology helpers to `GraphExtractor`.
- [ ] Add `GET /documents/graph` to the documents router.
- [ ] Verify backend graph tests pass.

### Task 2: Frontend Graph State Helpers

**Files:**
- Create: `frontend/src/app/graph/graphHealth.js`
- Create: `frontend/tests/graphHealth.test.mjs`

- [ ] Write Node tests for empty, unavailable, partial, and healthy graph states.
- [ ] Verify tests fail because helper is absent.
- [ ] Implement helper with no React dependencies.
- [ ] Verify frontend helper tests pass.

### Task 3: Graph Page UI

**Files:**
- Modify: `frontend/src/app/graph/page.tsx`

- [ ] Use typed graph payload from `/nexus-proxy/v1/documents/graph`.
- [ ] Render node/link visual distinctions for documents, chunks, entities, and relationships.
- [ ] Render clear empty, Neo4j unavailable, and partial extraction states.
- [ ] Verify `npx eslint src/app/graph/page.tsx` passes.

### Task 4: Final Verification And Publish

**Files:**
- Verify all changed files.

- [ ] Run `pytest -q` in `backend`.
- [ ] Run `node --test --no-warnings frontend/tests/graphHealth.test.mjs`.
- [ ] Run `npx eslint src/app/graph/page.tsx`.
- [ ] Commit and push the SAI-16 branch.
