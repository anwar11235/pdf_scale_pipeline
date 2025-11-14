"""Pydantic schemas for request/response"""
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID


class UploadResponse(BaseModel):
    doc_id: str
    status_url: str
    result_url: str
    presigned_url: Optional[str] = None


class UploadRequest(BaseModel):
    source: Optional[str] = None
    applicant_id: Optional[str] = None
    doc_type: Optional[str] = None


class StatusResponse(BaseModel):
    doc_id: str
    status: str
    current_step: Optional[str] = None
    progress_percent: float
    steps: List[Dict]
    created_at: datetime
    updated_at: datetime


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class PageResult(BaseModel):
    page_no: int
    text: Optional[str] = None
    confidence: Optional[float] = None
    bboxes: Optional[List[BoundingBox]] = None


class FieldResult(BaseModel):
    field_name: str
    field_value: Optional[str] = None
    confidence: Optional[float] = None
    page_no: Optional[int] = None


class TableResult(BaseModel):
    page_no: int
    data: List[List[str]]
    table_type: Optional[str] = None


class ResultResponse(BaseModel):
    doc_id: str
    filename: str
    status: str
    pages: List[PageResult]
    fields: List[FieldResult]
    tables: List[TableResult]
    metadata: Dict


class RetryRequest(BaseModel):
    step: Optional[str] = None


class FlaggedDocument(BaseModel):
    doc_id: str
    filename: str
    applicant_id: Optional[str] = None
    reason: str
    confidence: float
    created_at: datetime


class HumanReviewRequest(BaseModel):
    decision: str  # approve, approve_with_conditions, reject, request_more_docs
    comments: Optional[str] = None
    corrections: Optional[Dict[str, str]] = None
    conditions: Optional[str] = None

