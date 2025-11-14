"""Upload router"""
import os
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, Depends, Form
from sqlalchemy.orm import Session
from typing import Optional

from db.connection import get_db
from db.models import Document
from storage.s3_client import S3Client
from api.app.models.schemas import UploadResponse, UploadRequest
import redis
from rq import Queue

# Redis connection for queue
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_conn = redis.from_url(redis_url)
q = Queue('document_processing', connection=redis_conn)

def process_document_task(doc_id: str):
    """Task wrapper for RQ"""
    from db.connection import SessionLocal
    from workers.orchestrator import process_document
    import uuid
    
    db = SessionLocal()
    try:
        result = process_document(db, uuid.UUID(doc_id))
        return result
    finally:
        db.close()

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    source: Optional[str] = Form(None),
    applicant_id: Optional[str] = Form(None),
    doc_type: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a PDF document for processing"""
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise ValueError("Only PDF files are allowed")
    
    # Generate document ID
    doc_id = uuid.uuid4()
    
    # Store file in S3
    s3 = S3Client()
    s3_key = f"raw/{doc_id}.pdf"
    
    # Upload file
    s3.upload_file(file.file, s3_key, content_type="application/pdf")
    
    # Create document record
    document = Document(
        id=doc_id,
        filename=file.filename,
        s3_key=s3_key,
        status="queued",
        source=source,
        applicant_id=applicant_id,
        doc_type=doc_type
    )
    db.add(document)
    db.commit()
    
    # Enqueue processing task
    job = q.enqueue(process_document_task, str(doc_id))
    logger.info(f"Enqueued document {doc_id} for processing")
    
    # Generate presigned URL for direct upload (optional)
    presigned_url = s3.generate_presigned_url(s3_key, expiration=3600)
    
    return UploadResponse(
        doc_id=str(doc_id),
        status_url=f"/api/status/{doc_id}",
        result_url=f"/api/result/{doc_id}",
        presigned_url=presigned_url
    )

