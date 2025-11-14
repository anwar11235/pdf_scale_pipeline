"""AWS Textract adapter"""
import os
import logging
from typing import Dict
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class AWSTextractAdapter:
    """Adapter for AWS Textract"""
    
    def __init__(self):
        access_key = os.getenv("CLOUD_OCR_AWS_ACCESS_KEY")
        secret_key = os.getenv("CLOUD_OCR_AWS_SECRET")
        region = os.getenv("AWS_REGION", "us-east-1")
        
        if not access_key or not secret_key:
            logger.warning("AWS Textract credentials not configured")
            self.enabled = False
            return
        
        self.enabled = True
        self.client = boto3.client(
            'textract',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
    
    def analyze_document(self, bucket: str, key: str) -> Dict:
        """
        Analyze document using AWS Textract
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            Dict with pages, text, bboxes, confidences
        """
        if not self.enabled:
            return {"error": "AWS Textract not configured"}
        
        try:
            # Start document analysis
            response = self.client.start_document_analysis(
                DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': key}},
                FeatureTypes=['TABLES', 'FORMS']
            )
            
            job_id = response['JobId']
            
            # Wait for completion (in production, use async with status polling)
            import time
            while True:
                status_response = self.client.get_document_analysis(JobId=job_id)
                status = status_response['JobStatus']
                
                if status in ['SUCCEEDED', 'FAILED']:
                    break
                
                time.sleep(2)
            
            if status == 'FAILED':
                return {"error": "Textract job failed"}
            
            # Extract results
            pages = []
            blocks = status_response.get('Blocks', [])
            
            # Group blocks by page
            page_blocks = {}
            for block in blocks:
                page = block.get('Page', 1)
                if page not in page_blocks:
                    page_blocks[page] = []
                page_blocks[page].append(block)
            
            for page_num, blocks in page_blocks.items():
                page_text = ""
                bboxes = []
                confidences = []
                
                for block in blocks:
                    if block['BlockType'] == 'LINE':
                        text = block.get('Text', '')
                        page_text += text + "\n"
                        
                        geometry = block.get('Geometry', {})
                        bbox = geometry.get('BoundingBox', {})
                        if bbox:
                            bboxes.append({
                                "x1": bbox.get('Left', 0),
                                "y1": bbox.get('Top', 0),
                                "x2": bbox.get('Left', 0) + bbox.get('Width', 0),
                                "y2": bbox.get('Top', 0) + bbox.get('Height', 0)
                            })
                            confidences.append(block.get('Confidence', 90) / 100.0)
                
                pages.append({
                    "page_no": page_num,
                    "text": page_text.strip(),
                    "bboxes": bboxes,
                    "confidences": confidences,
                    "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.9
                })
            
            return {
                "pages": pages,
                "meta": {
                    "provider": "aws_textract",
                    "total_pages": len(pages)
                }
            }
        except ClientError as e:
            logger.error(f"AWS Textract error: {e}")
            return {"error": str(e)}


def analyze_document(bucket: str, key: str) -> Dict:
    """Convenience function"""
    adapter = AWSTextractAdapter()
    return adapter.analyze_document(bucket, key)

