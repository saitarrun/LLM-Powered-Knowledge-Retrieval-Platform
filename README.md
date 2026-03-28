# Nexus ~ LLM-Powered-Knowledge-Retrieval-Platform

[![Deployment - Vercel](https://img.shields.io/badge/Deployment-Vercel-black?style=for-the-badge&logo=vercel)](https://vercel.com)
[![Architecture - Swarm](https://img.shields.io/badge/Architecture-Swarm-gold?style=for-the-badge&logo=swarm)](https://github.com/saitarrun/rag-platform)

**Nexus** is an enterprise-grade, locally-sovereign Knowledge Retrieval Platform featuring a **Multi-Agent Swarm** architecture, **Knowledge Graph (Neo4j)** extraction, and **Local n8n Automation**. Designed for high-precision information extraction and curation.

### 🎯 Key Features
- **Multi-Agent Swarm Architecture**: Orchestrated AI agents working in concert for intelligent document processing
- **Knowledge Graph Visualization**: Neo4j-powered entity relationship mapping with interactive lattice visualization
- **Enterprise Security**: Multi-step approval workflows with Slack integration and role-based access control
- **Real-time Analytics**: Tactical dashboard monitoring asset health, vector density, and system performance
- **Intelligent Curation**: Grounded citations, feedback loops, and human-in-the-loop validation
- **Locally Sovereign**: Self-contained deployment with no external dependencies for data processing

## 🖼️ System Preview

### 📊 Tactical Dashboard
The central nervous system of the platform, providing real-time analytics on asset health, vector density, and system latency.
![Dashboard](./docs/screenshots/dashboard.png)

### 💬 Neural Chat Interface
Conversational intelligence with multi-agent orchestration. Features real-time streaming, grounded citations, and human-in-the-loop feedback.
![Chat](./docs/screenshots/chat.png)

### 🕸️ Neural Topology (GraphRAG)
Visualize the relationship between your data entities through the **Lattice Mapping**. High-importance hubs glow in gold, while minor synapses are rendered with high contrast.
![Topology](./docs/screenshots/topology.png)

### 📂 Knowledge Archive
Comprehensive document management with synchronization status and metadata extraction.
![Archive](./docs/screenshots/archive.png)

### 🔐 Multi-Step Approval (Slack & n8n)
Enterprise security via automated Slack approval workflows. No document enters the index without explicit authorization.
![Slack Approval](./docs/screenshots/slack_approval.png)
![n8n Workflow](./docs/screenshots/n8n.png)

## 🏗️ Architecture & Components

### Core Modules
- **Document Ingestion**: Intelligent preprocessing with PDF extraction, text chunking, and metadata enrichment
- **Vector Embeddings**: Semantic representation using configurable embedding models with FAISS indexing
- **Knowledge Graph**: Entity extraction and relationship mapping using Neo4j for semantic reasoning
- **Multi-Agent Orchestration**: Specialized agents for extraction, validation, curation, and response generation
- **Real-time Streaming**: WebSocket-based response streaming with progressive token delivery
- **Approval Workflows**: Human-in-the-loop validation with Slack notifications and n8n automation

### Data Flow
1. **Ingestion** → Document upload and preprocessing
2. **Extraction** → Multi-agent entity and relationship extraction
3. **Indexing** → Vector embeddings stored in FAISS, relationships in Neo4j
4. **Approval** → Slack-based review and authorization
5. **Retrieval** → Semantic search with graph-enhanced ranking
6. **Response** → Real-time streaming with citations and confidence scores

## ⚡ Quick Start

### Prerequisites
- Docker & Docker Compose
- 4GB+ available RAM
- OpenAI API key (for embeddings)

### 30-Second Setup
```bash
# Clone and configure
git clone https://github.com/saitarrun/LLM-Powered-Knowledge-Retrieval-Platform.git
cd LLM-Powered-Knowledge-Retrieval-Platform
cp .env.example .env
# Edit .env with your OpenAI API key

# Launch
docker-compose up -d

# Access the platform
open http://localhost:3001
```

## 🛠️ Tech Stack

- **Frontend**: Next.js 15+, Tailwind CSS 4, Framer Motion, D3-Force.
- **Backend**: FastAPI (Python 3.11), SQLAlchemy, FAISS, PyMuPDF.
- **Graph**: Neo4j 5.x.
- **Automation**: n8n (Locally containerized).
- **Cache**: Redis / GPTCache (Semantic Layer).

## 📡 API Documentation

### Core Endpoints

**Chat Completion with Citations**
```bash
POST /api/chat/completions
Content-Type: application/json

{
  "messages": [{"role": "user", "content": "Query"}],
  "model": "gpt-4",
  "stream": true,
  "context_limit": 5
}
```

**Document Upload**
```bash
POST /api/documents/upload
Content-Type: multipart/form-data

file: <PDF or TXT file>
metadata: {"source": "internal", "category": "technical"}
```

**Knowledge Graph Query**
```bash
GET /api/graph/entities?type=Person&limit=10
GET /api/graph/relationships?entity_id=123
```

**Index Health & Analytics**
```bash
GET /api/analytics/health
GET /api/analytics/vector-density
GET /api/analytics/top-entities
```

For comprehensive API documentation, visit `/api/docs` after starting the backend.

## 🚀 Deployment Strategy

### Local (Docker)
1. **Configure Environment**: Copy `.env.example` to `.env` and update with your API keys:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and other configuration
   ```

2. **Build and Start Services**: Launch all containers (backend, frontend, Redis, Neo4j, n8n):
   ```bash
   docker-compose up --build -d
   ```

3. **Access the Platform**:
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8001/api
   - Neo4j Browser: http://localhost:7474
   - n8n Workflows: http://localhost:5678
   - Redis: localhost:6380

4. **View Logs**:
   ```bash
   docker-compose logs -f backend  # Backend API logs
   docker-compose logs -f frontend # Frontend logs
   ```

5. **Stop Services**:
   ```bash
   docker-compose down
   ```

### Production (Vercel + Managed Backend)
1.  **Frontend**: Deploy the `frontend/` directory to Vercel.
2.  **Backend**: Host the `backend/` and `neo4j/` on a VPS (e.g., Railway).
3.  **Sync**: Connect via `NEXT_PUBLIC_API_URL`.

## 🤝 Contributing

We welcome contributions! Here's how to help:

1. **Fork & Clone**: Create a fork and clone to your machine
2. **Feature Branch**: `git checkout -b feature/your-feature`
3. **Development**: Make changes with clear commit messages
4. **Testing**: Run tests locally before pushing
5. **Pull Request**: Submit a PR with a clear description of changes

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend changes
- Include tests for new features
- Update documentation as needed
- Reference any relevant issues in your PR

## 📄 License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) file for details.

## 🙋 Support

- **Issues**: Report bugs or request features via GitHub Issues
- **Discussions**: Join community discussions in the Discussions tab
- **Documentation**: Check `/docs` folder for detailed guides

---
*Curated with ❤️ for the future of Agentic Intelligence.*
