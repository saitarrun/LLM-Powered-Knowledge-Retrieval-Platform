# Nexus ~ LLM-Powered-Knowledge-Retrieval-Platform

[![Deployment - Vercel](https://img.shields.io/badge/Deployment-Vercel-black?style=for-the-badge&logo=vercel)](https://vercel.com)
[![Architecture - Swarm](https://img.shields.io/badge/Architecture-Swarm-gold?style=for-the-badge&logo=swarm)](https://github.com/saitarrun/rag-platform)
[![Contributors](https://img.shields.io/github/contributors/saitarrun/LLM-Powered-Knowledge-Retrieval-Platform?style=for-the-badge)](https://github.com/saitarrun/LLM-Powered-Knowledge-Retrieval-Platform/graphs/contributors)
[![Open Issues](https://img.shields.io/github/issues/saitarrun/LLM-Powered-Knowledge-Retrieval-Platform?style=for-the-badge&color=orange)](https://github.com/saitarrun/LLM-Powered-Knowledge-Retrieval-Platform/issues)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

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

## 🤝 Contributing

We love contributors! Nexus is an open-source project and we welcome contributions of all types.

### Quick Start for Contributors
- **Setup Guide**: See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed setup and workflow
- **Good First Issues**: [Start here!](https://github.com/saitarrun/LLM-Powered-Knowledge-Retrieval-Platform/issues?q=label%3A%22good+first+issue%22) — Perfect for new contributors
- **Help Wanted**: [Issues needing attention](https://github.com/saitarrun/LLM-Powered-Knowledge-Retrieval-Platform/issues?q=label%3A%22help-wanted%22)
- **Discussion Board**: [Join the conversation](https://github.com/saitarrun/LLM-Powered-Knowledge-Retrieval-Platform/discussions)

### Areas We Need Help With
- **Backend**: FastAPI routes, agent orchestration, vector search optimization
- **Frontend**: React components, UI/UX improvements, real-time features
- **Testing**: pytest suite, E2E tests, integration tests
- **Documentation**: Architecture guides, API reference, deployment docs
- **DevOps**: CI/CD, observability, scaling infrastructure

**All skill levels welcome!** Start with documentation, tests, or "good first issue" items.

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

## ⚙️ Configuration

### Environment Variables
The platform requires several environment variables configured in `.env`:

**Backend Services**
- `OPENAI_API_KEY`: Your OpenAI API key for embeddings and LLM calls
- `BACKEND_PORT`: Port for FastAPI server (default: 8001)
- `LOG_LEVEL`: Logging level (debug, info, warning, error)

**Neo4j Graph Database**
- `NEO4J_PASSWORD`: Password for Neo4j admin user
- `NEO4J_PORT`: Neo4j Bolt port (default: 7687)

**Redis Cache**
- `REDIS_URL`: Redis connection URL (default: redis://redis:6379)
- `CACHE_TTL`: Cache time-to-live in seconds (default: 3600)

**Frontend Configuration**
- `NEXT_PUBLIC_API_URL`: Backend API endpoint
- `NEXT_PUBLIC_APP_NAME`: Application display name

**Slack Integration**
- `SLACK_BOT_TOKEN`: Slack app authentication token
- `SLACK_SIGNING_SECRET`: Slack request verification secret

**n8n Automation**
- `N8N_API_URL`: n8n API endpoint
- `N8N_API_KEY`: n8n API authentication key

See `.env.example` for a complete template with all available options.

## 🧪 Usage Examples

### Uploading Documents
```python
import requests

# Upload a document
with open("document.pdf", "rb") as f:
    files = {"file": f}
    metadata = {
        "source": "internal_docs",
        "category": "technical",
        "tags": ["api", "reference"]
    }
    response = requests.post(
        "http://localhost:8001/api/documents/upload",
        files=files,
        data={"metadata": str(metadata)}
    )
    print(response.json())
```

### Querying with Context
```python
import requests

# Ask a question with graph context
query = {
    "messages": [
        {"role": "user", "content": "What entities are related to our infrastructure?"}
    ],
    "model": "gpt-4",
    "stream": False,
    "context_limit": 10
}

response = requests.post(
    "http://localhost:8001/api/chat/completions",
    json=query
)
result = response.json()
print(result["choices"][0]["message"]["content"])
print(f"Citations: {result.get('citations', [])}")
```

### Exploring the Knowledge Graph
```bash
# Access Neo4j Browser
open http://localhost:7474

# Example Cypher query to find top entities
MATCH (e:Entity)
RETURN e.name, count(*) as relationships
ORDER BY relationships DESC
LIMIT 10
```

## 🐛 Troubleshooting

### Services Won't Start
**Issue**: Docker containers fail to start or exit immediately
- Check Docker is running: `docker ps`
- View logs: `docker-compose logs backend`
- Ensure ports 3001, 8001, 6379, 7474, 5678 are available
- Rebuild images: `docker-compose down && docker-compose up --build -d`

### Out of Memory Errors
**Issue**: "docker: Error response from daemon: OOMKilled"
- Increase Docker memory allocation (Docker Desktop → Preferences → Resources)
- Reduce batch size in `.env`: `BATCH_SIZE=32` (default: 64)
- Close other applications consuming memory

### Neo4j Connection Failures
**Issue**: Backend can't connect to Neo4j
- Verify Neo4j is running: `docker-compose ps neo4j`
- Check password matches in `.env`
- Wait 10-15 seconds for Neo4j to fully start after container creation
- Reset database: `docker-compose down -v && docker-compose up -d`

### Embedding Service Errors
**Issue**: "Invalid OpenAI API key" or embedding failures
- Verify your OpenAI API key in `.env`
- Check API key has embeddings permissions at openai.com/account/api-keys
- Ensure you have API credits available
- Try a smaller document first to test connectivity

### UI Not Loading
**Issue**: Frontend at localhost:3001 shows blank page
- Verify `NEXT_PUBLIC_API_URL` points to correct backend
- Check browser console for errors (F12 → Console)
- Clear browser cache and reload
- Rebuild frontend: `docker-compose down && docker-compose up --build frontend -d`

## 📚 Additional Resources

- **Full Documentation**: See `/docs` folder for detailed guides on architecture, workflows, and deployment
- **API Reference**: Interactive API docs at `http://localhost:8001/api/docs` (Swagger UI)
- **Video Tutorials**: [Coming soon] Complete walkthrough videos
- **Community Examples**: Check `/examples` folder for sample implementations

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

- ## 📚 Acknowledgments

- This project builds upon modern enterprise patterns for knowledge management and AI orchestration. Special thanks to the open-source communities behind Neo4j, LangChain, FastAPI, and Vercel for providing the foundational technologies that power Nexus.

- ---

**Built with ❤️ for semantic reasoning and knowledge curation**
- **Discussions**: Join community discussions in the Discussions tab
- **Documentation**: Check `/docs` folder for detailed guides

---
*Curated with ❤️ for the future of Agentic Intelligence.*
