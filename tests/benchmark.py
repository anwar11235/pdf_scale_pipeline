"""Benchmark script for OCR pipeline"""
import os
import sys
import csv
import time
import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from db.connection import SessionLocal, init_db
from db.models import Document, Page
from storage.s3_client import S3Client
from workers.orchestrator import process_document


def benchmark_pdfs(pdf_directory: str, output_csv: str = "benchmark_results.csv"):
    """
    Run pipeline on PDFs in directory and produce CSV report
    
    Args:
        pdf_directory: Directory containing PDF files
        output_csv: Output CSV file path
    """
    pdf_dir = Path(pdf_directory)
    if not pdf_dir.exists():
        print(f"Directory not found: {pdf_directory}")
        return
    
    # Initialize database
    init_db()
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}")
        return
    
    print(f"Found {len(pdf_files)} PDF files")
    
    results = []
    s3 = S3Client()
    db = SessionLocal()
    
    try:
        for pdf_file in pdf_files[:100]:  # Limit to 100 for benchmark
            print(f"Processing: {pdf_file.name}")
            
            # Create document record
            doc_id = uuid.uuid4()
            s3_key = f"raw/{doc_id}.pdf"
            
            # Upload to S3
            with open(pdf_file, 'rb') as f:
                s3.upload_file(f, s3_key, content_type="application/pdf")
            
            document = Document(
                id=doc_id,
                filename=pdf_file.name,
                s3_key=s3_key,
                status="queued"
            )
            db.add(document)
            db.commit()
            
            # Process document
            start_time = time.time()
            result = process_document(db, doc_id)
            elapsed_time = time.time() - start_time
            
            # Get results
            pages = db.query(Page).filter(Page.document_id == doc_id).all()
            total_chars = sum(len(p.ocr_text or p.native_text or "") for p in pages)
            avg_confidence = sum(p.ocr_confidence or 0 for p in pages) / len(pages) if pages else 0
            
            results.append({
                "doc_id": str(doc_id),
                "filename": pdf_file.name,
                "chars_extracted": total_chars,
                "avg_word_confidence": avg_confidence,
                "cer_estimate": None,  # Would need ground truth
                "time_seconds": elapsed_time,
                "status": result.get("success", False)
            })
            
            print(f"  Completed in {elapsed_time:.2f}s, {total_chars} chars")
    
    finally:
        db.close()
    
    # Write CSV
    with open(output_csv, 'w', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    print(f"\nBenchmark complete. Results written to {output_csv}")
    print(f"Processed {len(results)} documents")
    if results:
        avg_time = sum(r["time_seconds"] for r in results) / len(results)
        print(f"Average processing time: {avg_time:.2f}s")


if __name__ == "__main__":
    pdf_dir = sys.argv[1] if len(sys.argv) > 1 else "tests/samples"
    benchmark_pdfs(pdf_dir)

