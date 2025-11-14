"""Detect if PDF has native text layer"""
import fitz  # PyMuPDF
import logging
from typing import Tuple, Dict

logger = logging.getLogger(__name__)


def has_text_layer(pdf_path: str, threshold_chars: int = 50) -> Tuple[bool, Dict]:
    """
    Check if PDF has native text layer
    
    Args:
        pdf_path: Path to PDF file
        threshold_chars: Minimum number of characters to consider as having text
        
    Returns:
        Tuple of (has_text, metadata dict with text_length, fonts, etc.)
    """
    try:
        doc = fitz.open(pdf_path)
        total_chars = 0
        fonts = set()
        page_count = len(doc)
        
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            chars = len(text.strip())
            total_chars += chars
            
            # Extract font information
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            if "font" in span:
                                fonts.add(span["font"])
            
            if total_chars > threshold_chars:
                doc.close()
                return True, {
                    "text_length": total_chars,
                    "fonts": list(fonts),
                    "page_count": page_count,
                    "pages_checked": page_num + 1
                }
        
        doc.close()
        return False, {
            "text_length": total_chars,
            "fonts": list(fonts),
            "page_count": page_count,
            "pages_checked": page_count
        }
    except Exception as e:
        logger.error(f"Error detecting text layer: {e}")
        return False, {"error": str(e)}

