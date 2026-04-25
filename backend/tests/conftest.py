import pytest
import sys
import tempfile
import sqlite3
from unittest.mock import Mock, patch, MagicMock

# Mock heavy ML libraries before any imports
# This prevents ImportError when libraries aren't installed
for mod in [
    "sentence_transformers",
    "faiss",
    "rank_bm25",
    "neo4j",
    "celery",
    "redis",
    "langchain_text_splitters",
    "fitz",  # PyMuPDF
    "docx",  # python-docx
    "openai",
]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

# Mock submodules
sys.modules["faiss.swigfaiss"] = MagicMock()
sys.modules["langchain_text_splitters"] = MagicMock()
sys.modules["langchain_text_splitters.RecursiveCharacterTextSplitter"] = MagicMock()

# Now we can safely import app modules
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base
from app.db.database import get_db
from app.main import app


@pytest.fixture(scope="session")
def test_db():
    """Create a test database in memory."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    yield engine

    import os
    os.unlink(db_path)


@pytest.fixture
def db_session(test_db):
    """Create a database session for each test."""
    connection = test_db.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def override_app_db(db_session):
    """Route FastAPI dependency-injected DB access to the test transaction."""
    def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service that returns fixed embeddings."""
    with patch("app.services.embedding.embedding_service") as service_mock, \
         patch("app.ingestion.pipeline.embedding_service") as pipeline_mock:
        # Mock embed_one to return a 384-dimensional vector
        for mock in (service_mock, pipeline_mock):
            mock.embed_one.return_value = [0.1] * 384
            mock.embed.return_value = [[0.1] * 384, [0.2] * 384, [0.3] * 384]
            mock.dimension = 384
        yield pipeline_mock


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider."""
    with patch("app.services.llm_provider.llm_provider") as mock:
        mock.generate.return_value = "This is a test response."
        mock.generate_stream.return_value = iter(["This ", "is ", "a ", "test ", "response."])
        yield mock


@pytest.fixture
def mock_faiss_store():
    """Mock FAISS store."""
    with patch("app.vectorstore.faiss_store.FaissStore") as vectorstore_mock, \
         patch("app.ingestion.pipeline.FaissStore") as pipeline_mock:
        instance = MagicMock()
        instance.search.return_value = [
            {"score": 0.95, "metadata": {"chunk_id": "chunk1"}},
            {"score": 0.85, "metadata": {"chunk_id": "chunk2"}},
        ]
        instance.add_embeddings.return_value = None
        instance.remove.return_value = None
        vectorstore_mock.return_value = instance
        pipeline_mock.return_value = instance
        yield instance
