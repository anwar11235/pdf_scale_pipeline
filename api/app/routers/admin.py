"""Admin router for flagged documents and human review"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from db.connection import get_db
from db.models import Document, Field, AuditLog
from api.app.models.schemas import FlaggedDocument, HumanReviewRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/flagged", response_model=List[FlaggedDocument])
async def get_flagged_documents(db: Session = Depends(get_db)):
    """Get list of documents flagged for human review"""
    # Find documents with low confidence fields
    low_confidence_threshold = 0.7
    
    flagged_docs = []
    documents = db.query(Document).filter(Document.status == "flagged").all()
    
    for doc in documents:
        # Get average confidence
        fields = db.query(Field).filter(Field.document_id == doc.id).all()
        if fields:
            avg_confidence = sum(f.confidence or 0 for f in fields) / len(fields)
        else:
            avg_confidence = 0
        
        if avg_confidence < low_confidence_threshold:
            flagged_docs.append(FlaggedDocument(
                doc_id=str(doc.id),
                filename=doc.filename,
                applicant_id=doc.applicant_id,
                reason="Low confidence in extracted fields",
                confidence=avg_confidence,
                created_at=doc.created_at
            ))
    
    return flagged_docs


@router.post("/human_review/{doc_id}")
async def submit_human_review(
    doc_id: str,
    review: HumanReviewRequest,
    db: Session = Depends(get_db),
    user_id: str = None  # Would come from auth in production
):
    """Submit human review decision for a flagged document"""
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    
    document = db.query(Document).filter(Document.id == doc_uuid).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Apply corrections if provided
    if review.corrections:
        for field_name, field_value in review.corrections.items():
            field = db.query(Field).filter(
                Field.document_id == doc_uuid,
                Field.field_name == field_name
            ).first()
            
            if field:
                field.field_value = field_value
                field.confidence = 1.0  # Human-reviewed fields have max confidence
    
    # Update document status
    if review.decision == "approve":
        document.status = "approved"
    elif review.decision == "approve_with_conditions":
        document.status = "approved_with_conditions"
    elif review.decision == "reject":
        document.status = "rejected"
    elif review.decision == "request_more_docs":
        document.status = "pending_more_docs"
    
    # Create audit log
    audit_log = AuditLog(
        document_id=doc_uuid,
        action="human_review",
        user_id=UUID(user_id) if user_id else None,
        details={
            "decision": review.decision,
            "comments": review.comments,
            "conditions": review.conditions,
            "corrections": review.corrections
        }
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Review submitted successfully", "doc_id": doc_id, "status": document.status}

