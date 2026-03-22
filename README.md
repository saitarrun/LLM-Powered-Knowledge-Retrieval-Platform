# Nexus RAG Swarm Platform 🚀

An enterprise-grade, locally-sovereign Knowledge Retrieval Platform featuring a **Multi-Agent Swarm** architecture, **Knowledge Graph (Neo4j)** extraction, and **Local n8n Automation**.

## 🌟 Advanced Features
- **Swarm Orchestration**: Dynamic routing between Vector, Graph, SQL, and Web agents.
- **Hybrid Search**: Fusing BM25 Sparse and FAISS Dense vector results (RRF).
- **GraphRAG**: Automatic entity-relationship extraction stored in **Neo4j**.
- **Real-Time Streaming**: Token-level typewriter animation and agent observability tracing (SSE).
- **Local n8n Engine**: 100% local workflow automation for file sync and analytics.
- **Premium UI**: Interactive citations with document peek modals and Markdown rendering.

## 🛠️ Setup & Quickstart

1. **Start the Platform**:
   ```bash
   docker-compose up --build -d
   ```
2. **Access the Services**:
   - **Main UI**: [http://localhost:3001](http://localhost:3001)
   - **n8n Automation**: [http://localhost:5678](http://localhost:5678)
   - **Backend API**: [http://localhost:8001/api](http://localhost:8001/api)
   - **Graph UI (Neo4j)**: [http://localhost:7474](http://localhost:7474) (Login: neo4j/password)

## 📁 IDE Configuration
This workspace is optimized for **VS Code**:
- Extension recommendations and Python pathing are configured in `.vscode/settings.json`.
- A global `.gitignore` is provided to keep your environment clean.

## 🤖 Internal Swarm Agents
- **Query Understanding Agent**: Analyzing intent and resolving conversational memory.
- **Retriever Agent**: Multi-vector search with Reciprocal Rank Fusion.
- **Evidence Agent**: Neural reranking to ensure top-tier context precision.
- **Synthesis Agent**: Generating grounded, cited answers.
- **Critic Agent**: Real-time hallucination detection.
- **Web Search Agent**: Real-time DuckDuckGo lookup for current events.
- **SQL Analyst Agent**: Querying local metadata for admin insights.

---
*Created with ❤️ for Advanced Agentic Coding.*
