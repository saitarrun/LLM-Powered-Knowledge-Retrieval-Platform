# Contributing to Nexus

Thank you for your interest in contributing to **Nexus** — the multi-agent RAG platform! We welcome contributions of all types.

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Git

### Local Development Setup

1. **Fork and clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/LLM-Powered-Knowledge-Retrieval-Platform.git
cd LLM-Powered-Knowledge-Retrieval-Platform
```

2. **Set up environment:**
```bash
cp .env.example .env
```

3. **Start the full stack:**
```bash
docker compose up -d
```

4. **Verify everything is working:**
```bash
curl http://localhost:8001/api/v1/documents
open http://localhost:3001  # Frontend
open http://localhost:7474  # Neo4j
```

## 📋 Development Workflow

### 1. Find or Create an Issue
- Check [Issues](https://github.com/saitarrun/LLM-Powered-Knowledge-Retrieval-Platform/issues) for work
- Look for `good-first-issue` or `help-wanted` labels
- Discuss your idea before starting major work

### 2. Create a Feature Branch
```bash
git checkout -b feat/your-feature-name
```

Branch naming:
- `feat/` — new features
- `fix/` — bug fixes
- `docs/` — documentation
- `test/` — tests
- `refactor/` — improvements

### 3. Make Your Changes

**Backend (FastAPI):**
```bash
cd backend
# Code in app/
# Tests in app/tests/
```

**Frontend (Next.js):**
```bash
cd frontend/src
# Components in app/
# Tests in __tests__/
```

### 4. Test Your Changes
```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

### 5. Commit with Clear Messages
```bash
git commit -m "feat: add user authentication with JWT

- Implement JWT token generation
- Add protected routes middleware
- Include token refresh

Fixes #123"
```

Guidelines:
- Use present tense: "add" not "added"
- Be specific about what changed
- Reference issue numbers: `Fixes #123`
- First line under 70 characters

### 6. Push and Create a Pull Request
```bash
git push origin feat/your-feature-name
```

Include in PR description:
- What changed and why
- How to test changes
- Screenshots for UI changes

## 🏗️ Architecture Overview

### Backend (FastAPI)
```
backend/app/
├── main.py           # App initialization
├── api/              # Route handlers
│   ├── chat.py      # Chat endpoint
│   ├── documents.py # Document management
│   └── settings.py  # Configuration
├── core/             # Core utilities
├── db/               # Database models
├── agents/           # AI agents
└── services/         # Business logic
```

### Frontend (Next.js)
```
frontend/src/app/
├── page.tsx         # Home
├── chat/            # Chat interface
├── documents/       # Document management
└── components/      # Reusable components
```

### Stack
- **Backend**: FastAPI, SQLite/PostgreSQL
- **Frontend**: Next.js 16, React 19, Tailwind
- **Graph DB**: Neo4j
- **Vector DB**: FAISS (→ pgvector)
- **Queue**: Celery + Redis
- **Automation**: n8n

## 📝 Code Standards

### Python (Backend)
- **Style**: PEP 8
- **Type hints**: Use throughout
- **Docstrings**: Google-style

```python
from typing import List
from fastapi import APIRouter
from app.models import Document

router = APIRouter(tags=["documents"])

@router.get("/documents")
async def list_documents() -> List[Document]:
    """List all ingested documents.
    
    Returns:
        List of documents with metadata.
    """
    return []
```

### TypeScript/React (Frontend)
- **Components**: Functional with hooks
- **Props**: Type with interfaces
- **Naming**: PascalCase components, camelCase functions
- **Styling**: Tailwind classes

```typescript
interface DocumentCardProps {
  title: string;
  onDelete: () => void;
}

export function DocumentCard({ title, onDelete }: DocumentCardProps) {
  return (
    <div className="p-4 border rounded">
      <h3 className="font-bold">{title}</h3>
      <button onClick={onDelete} className="text-red-600">Delete</button>
    </div>
  );
}
```

## 🧪 Testing

### Running Tests
```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

### Writing Tests
- Focus on behavior, not implementation
- Add tests for new features
- Keep test maintenance in mind

## 📚 Documentation

Update docs when:
- Adding new features
- Changing architecture
- Adding API endpoints
- Updating deployment process

## 🐛 Reporting Bugs

Include:
- **Title**: Concise description
- **Environment**: OS, versions
- **Steps to reproduce**: Exact steps
- **Expected vs actual**: What should happen
- **Logs/error**: Full error messages

## 💡 Suggesting Features

Include:
- **Use case**: Why this matters
- **Proposed solution**: How it works
- **Alternatives**: Other approaches
- **Impact**: How many users benefit

## 🎯 How You Can Help

### For Beginners
- Look for `good-first-issue` label
- Improve documentation
- Add tests
- Report bugs with examples

### For Experienced Developers
- New features (auth, observability, etc.)
- Performance optimization
- Architecture improvements
- Mentoring

### For Everyone
- Report bugs
- Improve docs
- Answer questions
- Share use cases

## 📖 Resources

- **API Docs**: http://localhost:8001/api/v1/docs
- **Discussions**: [Project discussions](https://github.com/saitarrun/LLM-Powered-Knowledge-Retrieval-Platform/discussions)
- **Issues**: [Open issues](https://github.com/saitarrun/LLM-Powered-Knowledge-Retrieval-Platform/issues)

## ❓ Questions?

- **Setup help**: Create a discussion
- **General questions**: Post in discussions
- **Security issues**: Email maintainers privately

## 🎉 Recognition

Contributors are recognized in:
- README contributors section
- Release notes
- Monthly contributor spotlight

Thank you for contributing to Nexus! 🚀
