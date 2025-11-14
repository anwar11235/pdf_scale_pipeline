"""Main worker orchestration logic"""
import os
import logging
import uuid
import tempfile
from typing import Dict, Optional
from sqlalchemy.orm import Session

from datetime import datetime
from db.models import Document, Page, Field, Table, ProcessingCheckpoint
from storage.s3_client import S3Client
from classifier.detect_text_layer import has_text_layer
from preprocess.image_prep import preprocess_image
from layout.detect_layout import detect_layout, get_table_regions, get_text_regions
from ocr.ocr_workers.ocr_worker import ocr_pdf, extract_text_from_ocr_pdf
from extractor.tables import extract_tables_native
from postprocess.ner_extract import extract_fields, calculate_document_confidence
from ocr.ocr_adapters.google_docai import GoogleDocAIAdapter
from ocr.ocr_adapters.aws_textract import AWSTextractAdapter

logger = logging.getLogger(__name__)

# Processing steps
STEPS = [
    "classify",
    "preprocess",
    "layout",
    "ocr",
    "extract",
    "postprocess",
    "index",
    "complete"
]


def update_checkpoint(db: Session, doc_id: uuid.UUID, step: str, status: str, details: Optional[Dict] = None):
    """Update processing checkpoint"""
    checkpoint = db.query(ProcessingCheckpoint).filter(
        ProcessingCheckpoint.document_id == doc_id,
        ProcessingCheckpoint.step == step
    ).first()
    
    if checkpoint:
        checkpoint.status = status
        checkpoint.details = details or {}
        checkpoint.updated_at = datetime.utcnow()
    else:
        checkpoint = ProcessingCheckpoint(
            document_id=doc_id,
            step=step,
            status=status,
            details=details or {}
        )
        db.add(checkpoint)
    
    db.commit()


def process_document(db: Session, doc_id: uuid.UUID) -> Dict:
    """
    Main document processing orchestration
    
    Args:
        db: Database session
        doc_id: Document ID
        
    Returns:
        Processing result dict
    """
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        return {"error": "Document not found"}
    
    s3 = S3Client()
    ocr_confidence_threshold = float(os.getenv("OCR_CONF_THRESHOLD", "0.85"))
    
    try:
        # Step 1: Classify
        update_checkpoint(db, doc_id, "classify", "running")
        logger.info(f"Classifying document {doc_id}")
        
        # Download PDF from S3
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            s3.download_file(document.s3_key, tmp.name)
            pdf_path = tmp.name
        
        has_text, classify_meta = has_text_layer(pdf_path)
        update_checkpoint(db, doc_id, "classify", "complete", classify_meta)
        
        # Step 2: Process based on classification
        if has_text:
            # Native text PDF - extract directly
            import fitz
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                
                # Save page
                page_obj = Page(
                    document_id=doc_id,
                    page_no=page_num + 1,
                    native_text=text,
                    has_text_layer=True
                )
                db.add(page_obj)
            
            doc.close()
            db.commit()
            
            # Extract tables from native PDF
            update_checkpoint(db, doc_id, "extract", "running")
            tables = extract_tables_native(pdf_path)
            for table in tables:
                table_obj = Table(
                    document_id=doc_id,
                    page_no=table["page_no"],
                    extracted_rows_json=table["data"],
                    table_type=table.get("method")
                )
                db.add(table_obj)
            db.commit()
            update_checkpoint(db, doc_id, "extract", "complete")
        
        else:
            # Scanned PDF - need OCR
            # Step 2: Preprocess
            update_checkpoint(db, doc_id, "preprocess", "running")
            
            # Convert PDF pages to images
            import fitz
            doc = fitz.open(pdf_path)
            preprocessed_images = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_img:
                    pix.save(tmp_img.name)
                    img_path = tmp_img.name
                
                # Preprocess image
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_processed:
                    processed_img, prep_meta = preprocess_image(
                        img_path,
                        tmp_processed.name,
                        target_dpi=300
                    )
                    preprocessed_images.append(tmp_processed.name)
            
            doc.close()
            update_checkpoint(db, doc_id, "preprocess", "complete")
            
            # Step 3: Layout detection
            update_checkpoint(db, doc_id, "layout", "running")
            all_layouts = []
            for img_path in preprocessed_images:
                layout = detect_layout(img_path)
                all_layouts.append(layout)
            update_checkpoint(db, doc_id, "layout", "complete", {"pages": len(all_layouts)})
            
            # Step 4: OCR
            update_checkpoint(db, doc_id, "ocr", "running")
            ocr_result = ocr_pdf(pdf_path)
            
            if ocr_result["success"]:
                ocr_pages = extract_text_from_ocr_pdf(ocr_result["output_path"])
                
                for page_data in ocr_pages:
                    page_obj = Page(
                        document_id=doc_id,
                        page_no=page_data["page_no"],
                        ocr_text=page_data["text"],
                        ocr_confidence=page_data["confidence"],
                        has_text_layer=False
                    )
                    db.add(page_obj)
                db.commit()
            
            update_checkpoint(db, doc_id, "ocr", "complete")
        
        # Step 5: Postprocess - extract fields
        update_checkpoint(db, doc_id, "postprocess", "running")
        
        # Get all text from pages
        pages = db.query(Page).filter(Page.document_id == doc_id).all()
        full_text = "\n".join([p.ocr_text or p.native_text or "" for p in pages])
        
        # Extract fields
        extracted_fields = extract_fields(full_text)
        doc_confidence = calculate_document_confidence(extracted_fields)
        
        # Save fields
        for field in extracted_fields:
            field_obj = Field(
                document_id=doc_id,
                field_name=field["field_name"],
                field_value=field["field_value"],
                confidence=field["confidence"]
            )
            db.add(field_obj)
        db.commit()
        
        # Check if we need cloud OCR fallback
        if doc_confidence < ocr_confidence_threshold:
            logger.warning(f"Low confidence ({doc_confidence}), considering cloud OCR")
            # Could trigger cloud OCR here
        
        update_checkpoint(db, doc_id, "postprocess", "complete", {"confidence": doc_confidence})
        
        # Step 6: Index (placeholder - would index to Elasticsearch)
        update_checkpoint(db, doc_id, "index", "running")
        # TODO: Index to Elasticsearch
        update_checkpoint(db, doc_id, "index", "complete")
        
        # Step 7: Complete
        document.status = "complete"
        db.commit()
        update_checkpoint(db, doc_id, "complete", "complete")
        
        # Cleanup
        os.unlink(pdf_path)
        for img_path in preprocessed_images if 'preprocessed_images' in locals() else []:
            if os.path.exists(img_path):
                os.unlink(img_path)
        
        return {"success": True, "document_id": str(doc_id)}
    
    except Exception as e:
        logger.error(f"Error processing document {doc_id}: {e}", exc_info=True)
        document.status = "failed"
        db.commit()
        return {"error": str(e)}


from datetime import datetime

