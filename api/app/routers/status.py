"""Status router"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from db.connection import get_db
from db.models import Document, ProcessingCheckpoint
from api.app.models.schemas import StatusResponse

logger = logging.getLogger(__name__)

router = APIRouter()

STEPS = ["classify", "preprocess", "layout", "ocr", "extract", "postprocess", "index", "complete"]


@router.get("/status/{doc_id}", response_model=StatusResponse)
async def get_status(doc_id: str, db: Session = Depends(get_db)):
    """Get processing status for a document"""
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    
    document = db.query(Document).filter(Document.id == doc_uuid).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get checkpoints
    checkpoints = db.query(ProcessingCheckpoint).filter(
        ProcessingCheckpoint.document_id == doc_uuid
    ).all()
    
    checkpoint_dict = {cp.step: cp for cp in checkpoints}
    
    # Calculate progress
    completed_steps = [s for s in STEPS if s in checkpoint_dict and checkpoint_dict[s].status == "complete"]
    progress_percent = (len(completed_steps) / len(STEPS)) * 100
    
    # Get current step
    current_step = None
    for step in STEPS:
        if step in checkpoint_dict:
            if checkpoint_dict[step].status != "complete":
                current_step = step
                break
    
    # Build steps list
    steps = []
    for step in STEPS:
        if step in checkpoint_dict:
            cp = checkpoint_dict[step]
            steps.append({
                "step": step,
                "status": cp.status,
                "details": cp.details or {},
                "created_at": cp.created_at.isoformat(),
                "updated_at": cp.updated_at.isoformat()
            })
        else:
            steps.append({
                "step": step,
                "status": "pending",
                "details": {},
                "created_at": None,
                "updated_at": None
            })
    
    return StatusResponse(
        doc_id=str(doc_id),
        status=document.status,
        current_step=current_step,
        progress_percent=progress_percent,
        steps=steps,
        created_at=document.created_at,
        updated_at=document.updated_at
    )

