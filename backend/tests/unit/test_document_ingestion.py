import pytest
import tempfile
from unittest.mock import patch, MagicMock
from app.ingestion.pipeline import IngestionPipeline
from app.db.models import Document, DocumentChunk


MOCK_CHUNKS = [
    {"text": "This is test chunk 1.", "page_number": 1, "chunk_index": 0},
    {"text": "This is test chunk 2.", "page_number": 1, "chunk_index": 1},
]


@pytest.mark.asyncio
async def test_document_ingestion_success(db_session, mock_embedding_service, mock_faiss_store):
    """Test successful document ingestion pipeline."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is a test document. " * 50)
        file_path = f.name

    pipeline = IngestionPipeline()

    with patch("app.ingestion.pipeline.DocumentParser.parse") as mock_parse, \
         patch.object(pipeline.chunker, "chunk_document", return_value=MOCK_CHUNKS):
        mock_parse.return_value = [
            {"text": "This is a test document. " * 20, "page_number": 1}
        ]
        mock_embedding_service.embed.return_value = [[0.1] * 384] * len(MOCK_CHUNKS)

        status = await pipeline.ingest(
            file_path=file_path,
            filename="test.txt",
            doc_id="doc123",
            db=db_session,
            approval_required=False
        )

    assert status == "indexed"

    # Verify document was created
    doc = db_session.query(Document).filter(Document.id == "doc123").first()
    assert doc is not None
    assert doc.filename == "test.txt"
    assert doc.status == "indexed"


@pytest.mark.asyncio
async def test_document_ingestion_approval_required(db_session, mock_embedding_service):
    """Test document ingestion with approval required."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is a test document. " * 50)
        file_path = f.name

    pipeline = IngestionPipeline()

    with patch("app.ingestion.pipeline.DocumentParser.parse") as mock_parse, \
         patch.object(pipeline.chunker, "chunk_document", return_value=MOCK_CHUNKS):
        mock_parse.return_value = [
            {"text": "This is a test document. " * 20, "page_number": 1}
        ]
        mock_embedding_service.embed.return_value = [[0.1] * 384] * len(MOCK_CHUNKS)

        status = await pipeline.ingest(
            file_path=file_path,
            filename="test.txt",
            doc_id="doc123",
            db=db_session,
            approval_required=True
        )

    assert status == "pending"

    # Verify document has pending status
    doc = db_session.query(Document).filter(Document.id == "doc123").first()
    assert doc is not None
    assert doc.status == "pending"
    assert doc.approval_required is True


@pytest.mark.asyncio
async def test_document_ingestion_creates_chunks(db_session, mock_embedding_service):
    """Test that ingestion creates document chunks in database."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is a test document. " * 50)
        file_path = f.name

    pipeline = IngestionPipeline()

    with patch("app.ingestion.pipeline.DocumentParser.parse") as mock_parse, \
         patch.object(pipeline.chunker, "chunk_document", return_value=MOCK_CHUNKS):
        mock_parse.return_value = [
            {"text": "This is a test document. " * 20, "page_number": 1}
        ]
        mock_embedding_service.embed.return_value = [[0.1] * 384] * len(MOCK_CHUNKS)

        await pipeline.ingest(
            file_path=file_path,
            filename="test.txt",
            doc_id="doc123",
            db=db_session,
            approval_required=False
        )

    # Verify chunks were created
    chunks = db_session.query(DocumentChunk).filter(
        DocumentChunk.document_id == "doc123"
    ).all()

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.text is not None
        assert len(chunk.text) > 0


@pytest.mark.asyncio
async def test_document_ingestion_failure_sets_status(db_session):
    """Test that ingestion failure sets document status to 'failed'."""
    pipeline = IngestionPipeline()

    # Add document to database first
    doc = Document(id="doc123", filename="test.txt", status="processing")
    db_session.add(doc)
    db_session.commit()

    with patch("app.ingestion.pipeline.DocumentParser.parse") as mock_parse:
        mock_parse.return_value = []  # Empty result causes failure

        status = await pipeline.ingest(
            file_path="/nonexistent/file.txt",
            filename="test.txt",
            doc_id="doc123",
            db=db_session,
            approval_required=False
        )

    assert status == "failed"

    # Verify document status was updated
    doc = db_session.query(Document).filter(Document.id == "doc123").first()
    assert doc.status == "failed"
