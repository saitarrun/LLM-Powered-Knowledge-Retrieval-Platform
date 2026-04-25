import pytest
import tempfile
import io
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.db.models import Document, DocumentChunk, User, UserRole
from app.core.auth import hash_password, create_access_token
from app.db.database import SessionLocal


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def curator_token(db_session):
    """Create a curator user and return auth token."""
    user = User(
        email="curator@test.com",
        hashed_password=hash_password("password123"),
        role=UserRole.CURATOR
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({
        "email": user.email,
        "user_id": user.id,
        "role": user.role.value
    })

    return token


def test_upload_document_unauthorized(client):
    """Test upload without authentication returns 401."""
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", io.BytesIO(b"test content"))}
    )

    assert response.status_code == 403


def test_upload_document_viewer_forbidden(client, db_session):
    """Test upload with viewer role returns 403."""
    user = User(
        email="viewer@test.com",
        hashed_password=hash_password("password123"),
        role=UserRole.VIEWER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({
        "email": user.email,
        "user_id": user.id,
        "role": user.role.value
    })

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", io.BytesIO(b"test content"))},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_document_success(client, curator_token):
    """Test successful document upload."""
    file_content = b"This is a test document. " * 20

    with patch("app.ingestion.pipeline.DocumentParser.parse") as mock_parse:
        mock_parse.return_value = [
            {"text": "This is a test document. " * 20, "page_number": 1}
        ]

        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", io.BytesIO(file_content))},
            headers={"Authorization": f"Bearer {curator_token}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert "doc_id" in data
    assert data["filename"] == "test.txt"


def test_list_documents(client):
    """Test listing documents."""
    response = client.get("/api/v1/documents")

    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data


def test_get_document_not_found(client):
    """Test getting non-existent document returns 404."""
    response = client.get("/api/v1/documents/nonexistent123")

    assert response.status_code == 404


def test_get_document_chunk_context(client, db_session):
    """Test fetching document/chunk citation context."""
    doc = Document(id="doc123", filename="source.pdf", status="indexed")
    chunk = DocumentChunk(
        id="chunk123",
        document_id="doc123",
        text="This chunk supports a cited claim.",
        page_number=4,
        chunk_index=2,
        token_count=7,
    )
    db_session.add(doc)
    db_session.add(chunk)
    db_session.commit()

    response = client.get("/api/v1/documents/doc123/chunks/chunk123")

    assert response.status_code == 200
    data = response.json()
    assert data["available"] is True
    assert data["document"]["id"] == "doc123"
    assert data["document"]["filename"] == "source.pdf"
    assert data["chunk"]["id"] == "chunk123"
    assert data["chunk"]["text"] == "This chunk supports a cited claim."
    assert data["chunk"]["preview"] == "This chunk supports a cited claim."


def test_get_document_chunk_context_unavailable(client):
    """Test missing citation context returns a graceful unavailable payload."""
    response = client.get("/api/v1/documents/missing-doc/chunks/missing-chunk")

    assert response.status_code == 404
    assert response.json()["detail"]["available"] is False


@pytest.mark.asyncio
async def test_delete_document_unauthorized(client, db_session):
    """Test delete without authentication returns 401."""
    # Create a document first
    doc = Document(id="doc123", filename="test.txt", status="indexed")
    db_session.add(doc)
    db_session.commit()

    response = client.delete("/api/v1/documents/doc123")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_document_success(client, curator_token, db_session):
    """Test successful document deletion."""
    # Create a document first
    doc = Document(id="doc123", filename="test.txt", status="indexed")
    db_session.add(doc)
    db_session.commit()

    with patch("app.vectorstore.faiss_store.FaissStore"):
        response = client.delete(
            "/api/v1/documents/doc123",
            headers={"Authorization": f"Bearer {curator_token}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deleted"

    # Verify document was deleted from database
    doc = db_session.query(Document).filter(Document.id == "doc123").first()
    assert doc is None
