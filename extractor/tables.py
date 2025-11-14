"""Table extraction from PDFs"""
import logging
from typing import List, Dict, Optional
import pdfplumber
import camelot
import tempfile
import os

logger = logging.getLogger(__name__)


def extract_tables_native(pdf_path: str, page_no: Optional[int] = None) -> List[Dict]:
    """
    Extract tables from native PDF using PDFPlumber and Camelot
    
    Args:
        pdf_path: Path to PDF
        page_no: Specific page number (None for all pages)
        
    Returns:
        List of extracted tables
    """
    tables = []
    
    try:
        # Try PDFPlumber first
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_process = [page_no - 1] if page_no else range(len(pdf.pages))
            
            for pnum in pages_to_process:
                page = pdf.pages[pnum]
                page_tables = page.extract_tables()
                
                for table_idx, table in enumerate(page_tables):
                    if table:
                        tables.append({
                            "page_no": pnum + 1,
                            "table_no": table_idx + 1,
                            "method": "pdfplumber",
                            "data": table,
                            "row_count": len(table),
                            "col_count": len(table[0]) if table else 0
                        })
    except Exception as e:
        logger.warning(f"PDFPlumber extraction failed: {e}")
    
    # Try Camelot for lattice/stream tables
    try:
        if page_no:
            tables_camelot = camelot.read_pdf(pdf_path, pages=str(page_no), flavor='lattice')
        else:
            tables_camelot = camelot.read_pdf(pdf_path, flavor='lattice')
        
        for table in tables_camelot:
            tables.append({
                "page_no": table.page,
                "table_no": len([t for t in tables if t.get("page_no") == table.page]),
                "method": "camelot_lattice",
                "data": table.df.values.tolist(),
                "row_count": len(table.df),
                "col_count": len(table.df.columns),
                "accuracy": table.accuracy
            })
    except Exception as e:
        logger.warning(f"Camelot extraction failed: {e}")
    
    return tables


def extract_table_from_image(image_path: str, bbox: Optional[Dict] = None) -> Optional[Dict]:
    """
    Extract table from image region (for scanned PDFs)
    
    Args:
        image_path: Path to image
        bbox: Bounding box dict with x1, y1, x2, y2
        
    Returns:
        Extracted table dict or None
    """
    try:
        # Crop image to bbox if provided
        import cv2
        import numpy as np
        
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        if bbox:
            x1, y1 = int(bbox['x1']), int(bbox['y1'])
            x2, y2 = int(bbox['x2']), int(bbox['y2'])
            img = img[y1:y2, x1:x2]
        
        # Save cropped image temporarily
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            cv2.imwrite(tmp.name, img)
            tmp_path = tmp.name
        
        try:
            # Try Camelot on the image (requires conversion to PDF first)
            # For now, return None - in production, you might use a table detection model
            return None
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        logger.error(f"Error extracting table from image: {e}")
        return None

