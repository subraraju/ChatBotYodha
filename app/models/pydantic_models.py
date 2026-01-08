from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from decimal import Decimal


class CustomerBase(BaseModel):
    party_type: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    addr1: Optional[str] = None
    addr2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None
    country: Optional[str] = None
    comments: Optional[str] = None


class CustomerResponse(CustomerBase):
    customer_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    version: Optional[str] = None
    price: Optional[Decimal] = None
    stock_quantity: Optional[int] = None
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None
    comments: Optional[str] = None


class ProductResponse(ProductBase):
    product_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SalesBase(BaseModel):
    customer_id: int
    product_id: int
    quantity: Optional[int] = None
    sale_date: Optional[date] = None
    comments: Optional[str] = None
    total_amount: Optional[Decimal] = None


class SalesResponse(SalesBase):
    sale_id: int

    class Config:
        from_attributes = True


class ActivityBase(BaseModel):
    customer_id: int
    product_id: int
    activity_type: Optional[str] = None
    description: Optional[str] = None
    comments: Optional[str] = None


class ActivityResponse(ActivityBase):
    activity_id: int
    activity_date: datetime

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime


class ChatSession(BaseModel):
    session_id: str
    customer_email: str
    messages: list[ChatMessage]
    created_at: datetime
    updated_at: datetime


# Simple Chat API models for external integration
class SimpleChatRequest(BaseModel):
    message: str
    customer_email: Optional[str] = None


class SimpleChatResponse(BaseModel):
    response: str
    success: bool
