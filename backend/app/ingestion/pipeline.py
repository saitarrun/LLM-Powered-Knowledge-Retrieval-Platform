from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.db.models import Document, DocumentChunk
from app.ingestion.chunking.chunker import TextChunker
from app.ingestion.loaders.parser import DocumentParser
from app.services.embedding import embedding_service
from app.vectorstore.hybrid_store import HybridStore, hybrid_store


class IngestionPipeline:
    def __init__(self, store: HybridStore | None = None) -> None:
        self.parser = DocumentParser()
        self.chunker = TextChunker(
            parent_chunk_size=2000, child_chunk_size=400, overlap=50
        )
        self._store = store or hybrid_store
        logger.info("Initialized IngestionPipeline")

    async def ingest(
        self,
        file_path: str,
        filename: str,
        doc_id: str,
        db: Session,
        approval_required: bool = False,
    ) -> str:
        """Ingest document: parse → chunk → embed → DB insert → index."""
        try:
            logger.info(
                f"Starting ingestion for {filename} (doc_id={doc_id}, approval_required={approval_required})"
            )

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
                    parent_text=chunk.get("parent_text"),
                    page_number=chunk.get("page_number"),
                    chunk_index=chunk.get("chunk_index", 0),
                    token_count=len(chunk["text"].split()),
                )
                db_chunks.append(db_chunk)

            db.add_all(db_chunks)
            db.flush()

            logger.info(f"Created {len(db_chunks)} DB chunk records")

            # 4. Generate embeddings
            texts = [c.text for c in db_chunks]
            embeddings = embedding_service.embed(texts)
            logger.info(f"Generated {len(embeddings)} embeddings")

            # 5. Index to HybridStore (FAISS + BM25) unless approval required
            if not approval_required:
                chunk_ids = [c.id for c in db_chunks]
                self._store.add(
                    texts=texts,
                    ids=chunk_ids,
                    embeddings=embeddings,
                    metadatas=[{"chunk_id": c.id, "parent_text": c.parent_text} for c in db_chunks],
                )
                status = "indexed"
                indexed_at = datetime.utcnow()
                logger.info(f"Indexed {len(embeddings)} chunks via HybridStore")
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
