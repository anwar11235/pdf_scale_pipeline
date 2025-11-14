"""Primary OCR worker using OCRmyPDF/Tesseract"""
import os
import logging
import tempfile
from typing import Dict, List, Optional
import ocrmypdf

logger = logging.getLogger(__name__)


def ocr_pdf(
    pdf_path: str,
    output_path: Optional[str] = None,
    language: str = "eng",
    dpi: int = 300,
    skip_text: bool = False
) -> Dict:
    """
    Perform OCR on PDF using OCRmyPDF
    
    Args:
        pdf_path: Path to input PDF
        output_path: Path to output PDF (if None, creates temp file)
        language: Tesseract language code
        dpi: DPI for rendering
        skip_text: Skip pages that already have text
        
    Returns:
        Dict with OCR results and metadata
    """
    try:
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix='.pdf')
            os.close(fd)
        
        # OCR options
        ocr_options = {
            'language': language,
            'image_dpi': dpi,
            'skip_text': skip_text,
            'output_type': 'pdf',
            'force_ocr': not skip_text,
            'deskew': True,
            'clean': True,
            'remove_background': False
        }
        
        # Run OCR
        result = ocrmypdf.ocr(
            pdf_path,
            output_path,
            **ocr_options
        )
        
        return {
            "success": True,
            "output_path": output_path,
            "pages_processed": getattr(result, 'pages', 0),
            "metadata": {
                "language": language,
                "dpi": dpi
            }
        }
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return {
            "success": False,
            "error": str(e),
            "output_path": None
        }


def extract_text_from_ocr_pdf(pdf_path: str) -> List[Dict]:
    """
    Extract text and confidence from OCR'd PDF
    
    Returns:
        List of page dicts with text and confidence scores
    """
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(pdf_path)
        pages = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            
            # Try to extract confidence from OCR layer
            # Note: OCRmyPDF embeds confidence in some cases
            confidence = 0.85  # Default, could be improved
            
            pages.append({
                "page_no": page_num + 1,
                "text": text,
                "confidence": confidence,
                "char_count": len(text)
            })
        
        doc.close()
        return pages
    except Exception as e:
        logger.error(f"Error extracting text from OCR PDF: {e}")
        return []

