"""Azure Form Recognizer adapter"""
import os
import logging
from typing import Dict
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

logger = logging.getLogger(__name__)


class AzureFormRecognizerAdapter:
    """Adapter for Azure Form Recognizer"""
    
    def __init__(self):
        endpoint = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
        key = os.getenv("AZURE_FORM_RECOGNIZER_KEY")
        
        if not endpoint or not key:
            logger.warning("Azure Form Recognizer credentials not configured")
            self.enabled = False
            return
        
        self.enabled = True
        self.client = DocumentAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
    
    def analyze_document(self, bucket: str, key: str) -> Dict:
        """
        Analyze document using Azure Form Recognizer
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            Dict with pages, text, bboxes, confidences
        """
        if not self.enabled:
            return {"error": "Azure Form Recognizer not configured"}
        
        try:
            # Download from S3
            from storage.s3_client import S3Client
            s3 = S3Client()
            
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                s3.download_file(key, tmp.name)
                tmp_path = tmp.name
            
            # Read file
            with open(tmp_path, "rb") as f:
                file_content = f.read()
            
            # Analyze document
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-document",  # or use a custom model
                document=file_content
            )
            result = poller.result()
            
            # Extract results
            pages = []
            for page_num, page in enumerate(result.pages):
                page_text = ""
                bboxes = []
                confidences = []
                
                # Extract text from lines
                for line in page.lines:
                    page_text += line.content + "\n"
                    
                    # Get bounding box
                    if hasattr(line, 'polygon') and line.polygon:
                        bbox = {
                            "x1": min(p.x for p in line.polygon),
                            "y1": min(p.y for p in line.polygon),
                            "x2": max(p.x for p in line.polygon),
                            "y2": max(p.y for p in line.polygon)
                        }
                        bboxes.append(bbox)
                        confidences.append(0.9)  # Azure doesn't always provide confidence per line
                
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
                    "provider": "azure_form_recognizer",
                    "total_pages": len(pages)
                }
            }
        except Exception as e:
            logger.error(f"Azure Form Recognizer error: {e}")
            return {"error": str(e)}


def analyze_document(bucket: str, key: str) -> Dict:
    """Convenience function"""
    adapter = AzureFormRecognizerAdapter()
    return adapter.analyze_document(bucket, key)

