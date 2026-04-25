import os
from datetime import datetime
from sqlalchemy.orm import Session
from app.ingestion.loaders.parser import DocumentParser
from app.ingestion.chunking.chunker import TextChunker
from app.vectorstore.faiss_store import FaissStore
from app.services.embedding import embedding_service
from app.db.models import Document, DocumentChunk
from app.core.config import settings
from app.core.logging import logger


class IngestionPipeline:
    def __init__(self):
        self.parser = DocumentParser()
        self.chunker = TextChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        self.faiss_store = FaissStore(
            dimension=embedding_service.dimension,
            index_path=settings.FAISS_INDEX_PATH
        )
        logger.info("Initialized IngestionPipeline")

    async def ingest(
        self,
        file_path: str,
        filename: str,
        doc_id: str,
        db: Session,
        approval_required: bool = False
    ) -> str:
        """Ingest document: parse → chunk → embed → DB insert → FAISS index."""
        try:
            logger.info(f"Starting ingestion for {filename} (doc_id={doc_id}, approval_required={approval_required})")

            doc = db.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                doc = Document(
                    id=doc_id,
                    filename=filename,
                    file_path=file_path,
                    status="processing",
                    approval_required=approval_required,
                )
                db.add(doc)
                db.flush()

            # 1. Parse document
            pages = DocumentParser.parse(file_path, filename)
            if not pages:
                logger.warning(f"No pages extracted from {filename}")
                doc = db.query(Document).filter(Document.id == doc_id).first()
                if doc:
                    doc.status = "failed"
                    db.commit()
                return "failed"

            # 2. Chunk text
            chunks = self.chunker.chunk_document(pages)
            if not chunks:
                logger.warning(f"No chunks created from {filename}")
                doc = db.query(Document).filter(Document.id == doc_id).first()
                if doc:
                    doc.status = "failed"
                    db.commit()
                return "failed"

            logger.info(f"Created {len(chunks)} chunks from {filename}")

            # 3. Create DB chunk records
            db_chunks = []
            for chunk in chunks:
                db_chunk = DocumentChunk(
                    document_id=doc_id,
                    text=chunk["text"],
                    page_number=chunk.get("page_number"),
                    chunk_index=chunk.get("chunk_index", 0),
                    token_count=len(chunk["text"].split())
                )
                db_chunks.append(db_chunk)

            db.add_all(db_chunks)
            db.flush()  # Get IDs without committing

            logger.info(f"Created {len(db_chunks)} DB chunk records")

            # 4. Generate embeddings
            texts = [c.text for c in db_chunks]
            embeddings = embedding_service.embed(texts)
            logger.info(f"Generated {len(embeddings)} embeddings")

            # 5. Index to FAISS (unless approval required)
            if not approval_required:
                chunk_ids = [c.id for c in db_chunks]
                self.faiss_store.add_embeddings(embeddings, chunk_ids)
                status = "indexed"
                indexed_at = datetime.utcnow()
                logger.info(f"Indexed {len(embeddings)} embeddings to FAISS")
            else:
                status = "pending"
                indexed_at = None
                logger.info(f"Document {filename} marked for approval (status=pending)")

            # 6. Update document status
            doc.status = status
            doc.indexed_at = indexed_at
            db.commit()
            logger.info(f"Updated document status to {status}")

            return status

        except Exception as e:
            logger.error(f"Ingestion error for {filename}: {e}")
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                doc.status = "failed"
                db.commit()
            return "failed"


pipeline = IngestionPipeline()
