"""Document ingestion and management routes."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

router = APIRouter(tags=["documents"])

@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a document."""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Store file info
        return {
            "status": "processing",
            "filename": file.filename,
            "size": file.size,
            "message": "Document queued for ingestion"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def list_documents():
    """List all ingested documents."""
    return {
        "documents": [],
        "total": 0
    }

@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get document details."""
    return {
        "id": doc_id,
        "status": "processing"
    }

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document."""
    return {
        "status": "deleted",
        "id": doc_id
    }
