"""Document ingestion and management routes."""
import os
import shutil
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import Document, DocumentChunk, AuditLog
from app.core.config import settings
from app.core.logging import logger
from app.core.permissions import require_role, TokenData
from app.ingestion.pipeline import pipeline
from app.vectorstore.faiss_store import FaissStore
from app.services.embedding import embedding_service
from app.graph.extractor import graph_extractor

router = APIRouter(tags=["documents"])


@router.get("/documents/graph")
async def get_documents_graph():
    """Get knowledge graph topology and sanitized health status."""
    try:
        return await graph_extractor.get_topology_with_health()
    except Exception as e:
        logger.error(f"Graph endpoint error: {e}")
        return {
            "nodes": [],
            "links": [],
            "health": {
                "status": "unavailable",
                "neo4j_available": False,
                "node_count": 0,
                "relationship_count": 0,
                "document_count": 0,
                "chunk_count": 0,
                "entity_count": 0,
                "disconnected_document_count": 0,
                "partial_extraction": False,
                "errors": ["Graph service unavailable"],
            },
        }


class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    chunk_count: int
    indexed_at: Optional[str]
    approval_required: bool
    approved_by: Optional[str]

    class Config:
        from_attributes = True


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    approval_required: bool = False,
    current_user: TokenData = Depends(require_role(["curator", "admin"])),
    db: Session = Depends(get_db)
):
    """Upload and ingest a document."""
    try:
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Save file to disk
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Saved file to {file_path}")

        # Create document record
        doc = Document(
            filename=file.filename,
            content_type=file.content_type,
            file_path=file_path,
            status="processing",
            approval_required=approval_required
        )
        db.add(doc)
        db.flush()
        doc_id = doc.id

        # Ingest document (parse, chunk, embed, index)
        status = await pipeline.ingest(
            file_path=file_path,
            filename=file.filename,
            doc_id=doc_id,
            db=db,
            approval_required=approval_required
        )

        return {
            "status": status,
            "doc_id": doc_id,
            "filename": file.filename,
            "message": f"Document ingested with status={status}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(db: Session = Depends(get_db)):
    """List all ingested documents."""
    try:
        documents = db.query(Document).all()

        docs = []
        for doc in documents:
            chunk_count = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == doc.id
            ).count()
            docs.append({
                "id": doc.id,
                "filename": doc.filename,
                "status": doc.status,
                "chunk_count": chunk_count,
                "indexed_at": doc.indexed_at.isoformat() if doc.indexed_at else None,
                "approval_required": doc.approval_required,
                "approved_by": doc.approved_by,
                "created_at": doc.created_at.isoformat()
            })

        return {
            "documents": docs,
            "total": len(docs)
        }

    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str, db: Session = Depends(get_db)):
    """Get document details."""
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        chunk_count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc_id
        ).count()

        return {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status,
            "chunks": chunk_count,
            "created_at": doc.created_at.isoformat(),
            "indexed_at": doc.indexed_at.isoformat() if doc.indexed_at else None,
            "approval_required": doc.approval_required,
            "approved_by": doc.approved_by
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{doc_id}/chunks/{chunk_id}")
async def get_document_chunk_context(doc_id: str, chunk_id: str, db: Session = Depends(get_db)):
    """Get citation context for a document chunk."""
    try:
        chunk = db.query(DocumentChunk).filter(
            DocumentChunk.id == chunk_id,
            DocumentChunk.document_id == doc_id
        ).first()
        doc = db.query(Document).filter(Document.id == doc_id).first()

        if not chunk or not doc:
            raise HTTPException(
                status_code=404,
                detail={
                    "available": False,
                    "message": "Source document or chunk is unavailable",
                    "document_id": doc_id,
                    "chunk_id": chunk_id,
                }
            )

        preview = " ".join((chunk.text or "").split())
        if len(preview) > 500:
            preview = f"{preview[:497].rstrip()}..."

        return {
            "available": True,
            "document": {
                "id": doc.id,
                "filename": doc.filename,
                "status": doc.status,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "indexed_at": doc.indexed_at.isoformat() if doc.indexed_at else None,
            },
            "chunk": {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "text": chunk.text,
                "preview": preview,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document chunk context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: TokenData = Depends(require_role(["curator", "admin"])),
    db: Session = Depends(get_db)
):
    """Delete a document and its chunks."""
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get all chunks for this document to remove from FAISS
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == doc_id
        ).all()
        chunk_ids = [c.id for c in chunks]

        # Delete file from disk
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
                logger.info(f"Deleted file {doc.file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {doc.file_path}: {e}")

        # Remove from FAISS index
        if chunk_ids and doc.status == "indexed":
            try:
                faiss_store = FaissStore(
                    dimension=embedding_service.dimension,
                    index_path=settings.FAISS_INDEX_PATH
                )
                faiss_store.remove(chunk_ids)
                logger.info(f"Removed {len(chunk_ids)} chunks from FAISS index")
            except Exception as e:
                logger.warning(f"Failed to remove chunks from FAISS: {e}")

        # Create audit log
        audit_log = AuditLog(
            user_id=current_user.user_id,
            action="delete",
            resource_type="document",
            resource_id=doc_id,
            details=f"Document '{doc.filename}' deleted ({len(chunk_ids)} chunks removed)",
        )
        db.add(audit_log)

        # Delete from database (cascade deletes chunks)
        db.delete(doc)
        db.commit()

        logger.info(f"Deleted document {doc_id}")

        return {
            "status": "deleted",
            "id": doc_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
