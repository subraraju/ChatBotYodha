"""
Pydantic DTOs — request/response schemas for the API.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# ── Chat ──────────────────────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    customer_email: Optional[str] = None
    debug_mode: bool = False


class StartSessionResponse(BaseModel):
    session_id: str
    welcome_message: str


class MessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    debug_mode: bool = False


class MessageDTO(BaseModel):
    role: str
    content: str
    timestamp: str


class SessionInfoDTO(BaseModel):
    session_id: str
    customer_state: str
    customer_id: Optional[int] = None
    customer_info: Dict[str, Any] = {}
    recent_purchases: List[Dict[str, Any]] = []
    selected_product: Optional[Dict[str, Any]] = None
    messages: List[MessageDTO] = []
    debug_info: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    response: str
    session: SessionInfoDTO


class CloseSessionResponse(BaseModel):
    closing_message: str
    stored: bool


# ── Config ────────────────────────────────────────────────────────────

class ConfigResponse(BaseModel):
    company_name: str
    llm_provider: str
    embedding_model: str
    storage_backend: str


# ── Admin ─────────────────────────────────────────────────────────────

class DocUploadResponse(BaseModel):
    success: bool
    message: str
    files_processed: int = 0
    total_chunks: int = 0


# ── Customer CRUD ─────────────────────────────────────────────────────

class CustomerOut(BaseModel):
    customer_id: int
    party_type: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None

    model_config = {"from_attributes": True}


class ProductOut(BaseModel):
    product_id: int
    product_name: str
    category: Optional[str] = None
    type: Optional[str] = None
    price: float = 0
    stock_quantity: int = 0

    model_config = {"from_attributes": True}


class SaleOut(BaseModel):
    sales_id: int
    customer_id: int
    product_id: int
    quantity: int
    sale_date: Optional[str] = None
    total_amount: Optional[float] = None

    model_config = {"from_attributes": True}


# ── Marketing / Calendar ─────────────────────────────────────────────

class MarketingPersonOut(BaseModel):
    customer_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    model_config = {"from_attributes": True}


class TimeSlot(BaseModel):
    start: str
    end: str
    display: str


class BookMeetingRequest(BaseModel):
    marketing_person_id: int
    slot_index: int
    customer_name: str
    customer_email: str


class BookMeetingResponse(BaseModel):
    success: bool
    message: str
    meeting_id: Optional[str] = None
    calendar_link: Optional[str] = None
