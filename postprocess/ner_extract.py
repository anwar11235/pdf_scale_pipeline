"""NER and field extraction using spaCy and regex"""
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import spaCy
try:
    import spacy
    SPACY_AVAILABLE = True
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
        nlp = None
        SPACY_AVAILABLE = False
except ImportError:
    SPACY_AVAILABLE = False
    nlp = None
    logger.warning("spaCy not available")


# Regex patterns for common fields
PATTERNS = {
    "income": re.compile(r'\$?\d{1,3}(?:,\d{3})*(?:\.\d+)?'),
    "date": re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'),
    "ssn": re.compile(r'\d{3}-\d{2}-\d{4}'),
    "phone": re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "bank_account": re.compile(r'\b\d{4,17}\b'),  # Simple pattern
    "zip_code": re.compile(r'\b\d{5}(?:-\d{4})?\b'),
}


def extract_fields_regex(text: str) -> List[Dict]:
    """Extract fields using regex patterns"""
    fields = []
    
    for field_name, pattern in PATTERNS.items():
        matches = pattern.findall(text)
        for match in matches:
            fields.append({
                "field_name": field_name,
                "field_value": match,
                "confidence": 0.7,  # Regex matches have medium confidence
                "method": "regex"
            })
    
    return fields


def extract_fields_spacy(text: str) -> List[Dict]:
    """Extract fields using spaCy NER"""
    if not SPACY_AVAILABLE or nlp is None:
        return []
    
    try:
        doc = nlp(text)
        fields = []
        
        for ent in doc.ents:
            # Map spaCy labels to our field names
            field_mapping = {
                "PERSON": "person_name",
                "ORG": "organization",
                "GPE": "location",
                "DATE": "date",
                "MONEY": "income",
                "EMAIL": "email",
                "PHONE": "phone"
            }
            
            field_name = field_mapping.get(ent.label_, ent.label_.lower())
            fields.append({
                "field_name": field_name,
                "field_value": ent.text,
                "confidence": 0.85,  # spaCy confidence
                "method": "spacy",
                "label": ent.label_
            })
        
        return fields
    except Exception as e:
        logger.error(f"spaCy extraction error: {e}")
        return []


def normalize_date(date_str: str) -> Optional[str]:
    """Normalize date to ISO format"""
    try:
        # Try various date formats
        formats = [
            "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%d-%m-%Y",
            "%Y-%m-%d", "%m/%d/%y", "%d/%m/%y"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        return date_str
    except Exception:
        return date_str


def extract_fields(text: str, use_spacy: bool = True) -> List[Dict]:
    """
    Extract structured fields from text
    
    Args:
        text: Input text
        use_spacy: Whether to use spaCy NER
        
    Returns:
        List of extracted fields with confidence scores
    """
    fields = []
    
    # Extract using regex
    fields.extend(extract_fields_regex(text))
    
    # Extract using spaCy if available
    if use_spacy:
        fields.extend(extract_fields_spacy(text))
    
    # Normalize dates
    for field in fields:
        if field["field_name"] == "date":
            normalized = normalize_date(field["field_value"])
            field["field_value"] = normalized
    
    # Deduplicate (keep highest confidence)
    seen = {}
    for field in fields:
        key = (field["field_name"], field["field_value"])
        if key not in seen or field["confidence"] > seen[key]["confidence"]:
            seen[key] = field
    
    return list(seen.values())


def calculate_document_confidence(fields: List[Dict]) -> float:
    """Calculate overall document confidence from field confidences"""
    if not fields:
        return 0.0
    
    confidences = [f["confidence"] for f in fields]
    return sum(confidences) / len(confidences)

