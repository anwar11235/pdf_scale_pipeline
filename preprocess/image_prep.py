"""Image preprocessing: deskew, denoise, resize to 300 DPI, binarize"""
import cv2
import numpy as np
from PIL import Image
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def deskew(image: np.ndarray) -> np.ndarray:
    """Deskew an image using Hough transform"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    
    if lines is None or len(lines) == 0:
        return image
    
    angles = []
    for rho, theta in lines[:20]:  # Check first 20 lines
        angle = (theta * 180 / np.pi) - 90
        if -45 < angle < 45:
            angles.append(angle)
    
    if not angles:
        return image
    
    median_angle = np.median(angles)
    if abs(median_angle) < 0.5:  # Skip if angle is very small
        return image
    
    # Rotate image
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated


def denoise(image: np.ndarray) -> np.ndarray:
    """Remove noise from image"""
    if len(image.shape) == 3:
        return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
    else:
        return cv2.fastNlMeansDenoising(image, None, 10, 7, 21)


def resize_to_dpi(image: np.ndarray, target_dpi: int = 300, current_dpi: int = 72) -> np.ndarray:
    """Resize image to target DPI"""
    if current_dpi == target_dpi:
        return image
    
    scale_factor = target_dpi / current_dpi
    height, width = image.shape[:2]
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)


def binarize(image: np.ndarray, method: str = "adaptive") -> np.ndarray:
    """Binarize image (convert to black and white)"""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    if method == "adaptive":
        return cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
    elif method == "otsu":
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    else:
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        return binary


def crop_borders(image: np.ndarray, margin: int = 10) -> np.ndarray:
    """Crop borders from image"""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Find non-zero regions
    coords = cv2.findNonZero(gray)
    if coords is None:
        return image
    
    x, y, w, h = cv2.boundingRect(coords)
    return image[max(0, y-margin):min(image.shape[0], y+h+margin),
                 max(0, x-margin):min(image.shape[1], x+w+margin)]


def preprocess_image(
    image_path: str,
    output_path: str,
    target_dpi: int = 300,
    current_dpi: int = 72,
    apply_deskew: bool = True,
    apply_denoise: bool = True,
    apply_binarize: bool = True
) -> Tuple[np.ndarray, dict]:
    """
    Full image preprocessing pipeline
    
    Returns:
        Tuple of (processed_image, metadata dict)
    """
    try:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        original_shape = img.shape
        metadata = {"original_shape": original_shape, "steps_applied": []}
        
        # Apply preprocessing steps
        if apply_deskew:
            img = deskew(img)
            metadata["steps_applied"].append("deskew")
        
        if apply_denoise:
            img = denoise(img)
            metadata["steps_applied"].append("denoise")
        
        img = resize_to_dpi(img, target_dpi, current_dpi)
        metadata["steps_applied"].append(f"resize_to_{target_dpi}dpi")
        metadata["resized_shape"] = img.shape
        
        if apply_binarize:
            img = binarize(img)
            metadata["steps_applied"].append("binarize")
        
        # Save processed image
        cv2.imwrite(output_path, img)
        metadata["output_path"] = output_path
        
        return img, metadata
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        raise

