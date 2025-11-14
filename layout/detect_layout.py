"""Layout detection using LayoutParser"""
import logging
from typing import List, Dict, Optional
import numpy as np
from PIL import Image
import cv2

logger = logging.getLogger(__name__)

try:
    import layoutparser as lp
    LAYOUTPARSER_AVAILABLE = True
except ImportError:
    LAYOUTPARSER_AVAILABLE = False
    logger.warning("LayoutParser not available. Install with: pip install layoutparser[paddlepaddle]")


def detect_layout(image_path: str, model_name: str = "PubLayNet") -> List[Dict]:
    """
    Detect layout elements in an image
    
    Args:
        image_path: Path to image file
        model_name: Model to use (PubLayNet, etc.)
        
    Returns:
        List of detected layout elements with bboxes and types
    """
    if not LAYOUTPARSER_AVAILABLE:
        logger.warning("LayoutParser not available, returning empty layout")
        return []
    
    try:
        # Load model (will download on first use)
        if model_name == "PubLayNet":
            model = lp.PaddleDetectionLayoutModel(
                config_path="lp://PubLayNet/ppyolov2_r50vd_dcn_365e_publaynet/config",
                threshold=0.5,
                label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
            )
        else:
            model = lp.AutoLayoutModel(model_name)
        
        # Load and process image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect layout
        layout = model.detect(image_rgb)
        
        # Convert to list of dicts
        results = []
        for element in layout:
            bbox = element.block
            results.append({
                "type": element.type,
                "bbox": {
                    "x1": float(bbox.x_1),
                    "y1": float(bbox.y_1),
                    "x2": float(bbox.x_2),
                    "y2": float(bbox.y_2)
                },
                "confidence": float(element.score) if hasattr(element, 'score') else 1.0
            })
        
        return results
    except Exception as e:
        logger.error(f"Error detecting layout: {e}")
        return []


def get_table_regions(layout_results: List[Dict]) -> List[Dict]:
    """Extract table regions from layout results"""
    return [r for r in layout_results if r["type"].lower() == "table"]


def get_text_regions(layout_results: List[Dict]) -> List[Dict]:
    """Extract text regions from layout results"""
    text_types = ["text", "title", "list"]
    return [r for r in layout_results if r["type"].lower() in text_types]

