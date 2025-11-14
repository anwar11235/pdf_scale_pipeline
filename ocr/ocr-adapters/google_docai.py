"""Google Document AI adapter"""
import os
import logging
from typing import Dict, List, Optional
from google.cloud import documentai

logger = logging.getLogger(__name__)


class GoogleDocAIAdapter:
    """Adapter for Google Document AI"""
    
    def __init__(self):
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us")
        processor_id = os.getenv("GOOGLE_DOCAI_PROCESSOR_ID")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if not project_id or not processor_id:
            logger.warning("Google Document AI credentials not configured")
            self.enabled = False
            return
        
        self.enabled = True
        self.client = documentai.DocumentProcessorServiceClient()
        self.processor_name = self.client.processor_path(project_id, location, processor_id)
    
    def analyze_document(self, bucket: str, key: str) -> Dict:
        """
        Analyze document using Google Document AI
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            Dict with pages, text, bboxes, confidences
        """
        if not self.enabled:
            return {"error": "Google Document AI not configured"}
        
        try:
            # For this implementation, we'd need to download from S3 first
            # In production, you might use GCS directly or download to temp file
            from storage.s3_client import S3Client
            s3 = S3Client()
            
            # Download to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                s3.download_file(key, tmp.name)
                tmp_path = tmp.name
            
            # Read file
            with open(tmp_path, "rb") as f:
                file_content = f.read()
            
            # Process document
            raw_document = documentai.RawDocument(
                content=file_content,
                mime_type="application/pdf"
            )
            
            request = documentai.ProcessRequest(
                name=self.processor_name,
                raw_document=raw_document
            )
            
            result = self.client.process_document(request=request)
            document = result.document
            
            # Extract results
            pages = []
            for page_num, page in enumerate(document.pages):
                page_text = ""
                bboxes = []
                confidences = []
                
                # Extract text and bounding boxes
                for block in page.blocks:
                    block_text = ""
                    for paragraph in block.paragraphs:
                        for word in paragraph.words:
                            word_text = "".join([symbol.text for symbol in word.symbols])
                            block_text += word_text + " "
                            
                            # Get bounding box
                            vertices = word.layout.bounding_poly.vertices
                            if vertices:
                                bboxes.append({
                                    "x1": vertices[0].x,
                                    "y1": vertices[0].y,
                                    "x2": vertices[-1].x,
                                    "y2": vertices[-1].y
                                })
                                confidences.append(word.layout.confidence if hasattr(word.layout, 'confidence') else 0.9)
                    
                    page_text += block_text
                
                pages.append({
                    "page_no": page_num + 1,
                    "text": page_text.strip(),
                    "bboxes": bboxes,
                    "confidences": confidences,
                    "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.9
                })
            
            # Cleanup
            os.unlink(tmp_path)
            
            return {
                "pages": pages,
                "meta": {
                    "provider": "google_document_ai",
                    "total_pages": len(pages)
                }
            }
        except Exception as e:
            logger.error(f"Google Document AI error: {e}")
            return {"error": str(e)}


def analyze_document(bucket: str, key: str) -> Dict:
    """Convenience function"""
    adapter = GoogleDocAIAdapter()
    return adapter.analyze_document(bucket, key)

