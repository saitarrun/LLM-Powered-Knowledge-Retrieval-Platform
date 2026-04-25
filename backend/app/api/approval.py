from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import List
from app.db.database import get_db
from app.db.models import Document, DocumentChunk, AuditLog, UserRole
from app.core.permissions import require_role, TokenData
from app.core.config import settings
from app.services.embedding import embedding_service
from app.vectorstore.faiss_store import FaissStore

router = APIRouter(tags=["approval"])
faiss_store = FaissStore(
    dimension=embedding_service.dimension,
    index_path=settings.FAISS_INDEX_PATH,
)


class DocumentPreview(BaseModel):
    id: str
    filename: str
    status: str
    approval_required: bool
    created_at: str
    preview: str  # First 500 chars of first chunk


class ApprovalRequest(BaseModel):
    reason: str = None


@router.get("/documents/pending", response_model=List[DocumentPreview])
async def list_pending_documents(
    current_user: TokenData = Depends(require_role(["curator", "admin"])),
    db: Session = Depends(get_db),
):
    # Get documents with status="pending"
    pending_docs = db.query(Document).filter(Document.status == "pending").all()

    result = []
    for doc in pending_docs:
        # Get first chunk for preview
        first_chunk = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == doc.id)
            .order_by(DocumentChunk.chunk_index)
            .first()
        )
        preview = first_chunk.text[:500] if first_chunk else ""

        result.append(
            DocumentPreview(
                id=doc.id,
                filename=doc.filename,
                status=doc.status,
                approval_required=doc.approval_required,
                created_at=doc.created_at.isoformat(),
                preview=preview,
            )
        )

    return result


@router.post("/documents/{doc_id}/approve")
async def approve_document(
    doc_id: str,
    current_user: TokenData = Depends(require_role(["curator", "admin"])),
    db: Session = Depends(get_db),
):
    # Get document
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Verify document is pending
    if doc.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document status is '{doc.status}', must be 'pending' to approve",
        )

    # Get all chunks for this document
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == doc_id)
        .all()
    )

    # Generate embeddings if not already done
    chunk_embeddings = []
    chunk_ids = []
    for chunk in chunks:
        if chunk.embedding_id:
            # Embedding already exists, skip re-embedding
            chunk_embeddings.append(None)
        else:
            # Generate embedding for this chunk
            embedding = embedding_service.embed_one(chunk.text)
            chunk_embeddings.append(embedding)
        chunk_ids.append(chunk.id)

    # Add to FAISS index
    embeddings_to_add = []
    chunk_ids_to_add = []
    for i, embedding in enumerate(chunk_embeddings):
        if embedding is not None:
            embeddings_to_add.append(embedding)
            chunk_ids_to_add.append(chunks[i].id)

    if embeddings_to_add:
        faiss_store.add_embeddings(embeddings_to_add, chunk_ids_to_add)
        for chunk in chunks:
            if chunk.id in chunk_ids_to_add:
                chunk.embedding_id = chunk.id

    # Update document status
    doc.status = "indexed"
    doc.approved_by = current_user.email
    doc.approved_at = datetime.utcnow()
    doc.indexed_at = datetime.utcnow()

    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.user_id,
        action="approve",
        resource_type="document",
        resource_id=doc_id,
        details=f"Document '{doc.filename}' approved for indexing",
    )
    db.add(audit_log)
    db.commit()

    return {"status": "approved", "document_id": doc_id}


@router.post("/documents/{doc_id}/reject")
async def reject_document(
    doc_id: str,
    request: ApprovalRequest,
    current_user: TokenData = Depends(require_role(["curator", "admin"])),
    db: Session = Depends(get_db),
):
    # Get document
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Verify document is pending
    if doc.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document status is '{doc.status}', must be 'pending' to reject",
        )

    # Update document status
    doc.status = "rejected"

    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.user_id,
        action="reject",
        resource_type="document",
        resource_id=doc_id,
        details=f"Document '{doc.filename}' rejected. Reason: {request.reason or 'No reason provided'}",
    )
    db.add(audit_log)
    db.commit()

    return {"status": "rejected", "document_id": doc_id}
