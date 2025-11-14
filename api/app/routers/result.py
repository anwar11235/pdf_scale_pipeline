"""Result router"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from db.connection import get_db
from db.models import Document, Page, Field, Table
from api.app.models.schemas import ResultResponse, PageResult, FieldResult, TableResult, BoundingBox

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/result/{doc_id}", response_model=ResultResponse)
async def get_result(doc_id: str, db: Session = Depends(get_db)):
    """Get processing results for a document"""
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    
    document = db.query(Document).filter(Document.id == doc_uuid).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get pages
    pages = db.query(Page).filter(Page.document_id == doc_uuid).order_by(Page.page_no).all()
    page_results = []
    for page in pages:
        page_results.append(PageResult(
            page_no=page.page_no,
            text=page.ocr_text or page.native_text,
            confidence=page.ocr_confidence,
            bboxes=None  # Could be populated from OCR results
        ))
    
    # Get fields
    fields = db.query(Field).filter(Field.document_id == doc_uuid).all()
    field_results = []
    for field in fields:
        field_results.append(FieldResult(
            field_name=field.field_name,
            field_value=field.field_value,
            confidence=field.confidence,
            page_no=field.page_no
        ))
    
    # Get tables
    tables = db.query(Table).filter(Table.document_id == doc_uuid).all()
    table_results = []
    for table in tables:
        table_results.append(TableResult(
            page_no=table.page_no,
            data=table.extracted_rows_json or [],
            table_type=table.table_type
        ))
    
    return ResultResponse(
        doc_id=str(doc_id),
        filename=document.filename,
        status=document.status,
        pages=page_results,
        fields=field_results,
        tables=table_results,
        metadata={
            "source": document.source,
            "applicant_id": document.applicant_id,
            "doc_type": document.doc_type,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat()
        }
    )


@router.post("/retry/{doc_id}")
async def retry_document(doc_id: str, step: str = None, db: Session = Depends(get_db)):
    """Retry processing a document, optionally from a specific step"""
    try:
        doc_uuid = UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    
    document = db.query(Document).filter(Document.id == doc_uuid).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Reset status and enqueue
    document.status = "queued"
    db.commit()
    
    from worker_orchestration.consumer import q, process_document_task
    job = q.enqueue(process_document_task, str(doc_id))
    
    return {"message": "Document queued for reprocessing", "doc_id": doc_id, "job_id": job.id}

