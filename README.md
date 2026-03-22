# Nexus ⚡ RAG Swarm Platform

[![Deployment - Vercel](https://img.shields.io/badge/Deployment-Vercel-black?style=for-the-badge&logo=vercel)](https://vercel.com)
[![Architecture - Swarm](https://img.shields.io/badge/Architecture-Swarm-gold?style=for-the-badge&logo=swarm)](https://github.com/saitarrun/rag-platform)

**Nexus** is an enterprise-grade, locally-sovereign Knowledge Retrieval Platform featuring a **Multi-Agent Swarm** architecture, **Knowledge Graph (Neo4j)** extraction, and **Local n8n Automation**. Designed for high-precision information extraction and curation.

## 🌟 Key Features

### 🧠 Swarm Orchestration
A dynamic multi-agent system that routes queries through specialized neural nodes:
- **Orchestration Agent**: Logic-driven routing and intent resolution.
- **Evidence Agent**: Neural reranking to ensure top-tier context precision.
- **Synthesis Agent**: Generating grounded, cited answers with zero hallucinations.
- **Feedback Agent**: Human-in-the-loop correction and reinforcement.

### 🕸️ Neural Topology (GraphRAG)
Automatic entity-relationship extraction stored in **Neo4j**. Visualize the system's "memory" with the **Lattice Mapping** interface, featuring color-graded importance and level-of-detail rendering.

### 🔍 Hybrid Retrieval
Fusing **BM25 Sparse** and **FAISS Dense** vector results using **Reciprocal Rank Fusion (RRF)** for the ultimate retrieval accuracy.

### 🎨 Premium Semantic UI
- **Lattice Design System**: A high-contrast, professional dark theme (`#050505`).
- **Real-time Observability**: Trace agent execution and performance in real-time.
- **Interactive Citations**: Perfectly relevant document references with instant document peek modals.

## 🛠️ Tech Stack

- **Frontend**: Next.js 15+, Tailwind CSS 4, Framer Motion, D3-Force.
- **Backend**: FastAPI (Python 3.11), SQLAlchemy, FAISS, PyMuPDF.
- **Graph**: Neo4j 5.x.
- **Automation**: n8n (Locally containerized).
- **Cache**: Redis / GPTCache (Semantic Layer).

## 🚀 Deployment Strategy

### Local (Docker)
The system is fully containerized and easy to run anywhere:
```bash
docker-compose up --build -d
```

### Production (Vercel + Managed Backend)
1.  **Frontend**: Deploy the `frontend/` directory to Vercel.
2.  **Backend**: Host the `backend/` and `neo4j/` on a VPS (e.g., Railway, Render, AWS) to maintain persistent state.
3.  **Sync**: Connect the frontend to the backend via `NEXT_PUBLIC_API_URL`.

---
*Curated with ❤️ for the future of Agentic Intelligence.*
