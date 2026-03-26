"""
SQLAlchemy ORM models — 4 tables: customer, product, sales, activity.

Marketing persons live in the customer table with party_type='MKTG'.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Integer, BigInteger, String, DateTime, Date, Text,
    ForeignKey, Numeric, Boolean,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


# ── Customer ──────────────────────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customer"

    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    party_type: Mapped[Optional[str]] = mapped_column(String(20))  # Individual / Business / MKTG
    first_name: Mapped[Optional[str]] = mapped_column(String(50))
    last_name: Mapped[Optional[str]] = mapped_column(String(50))
    middle_name: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    addr1: Mapped[Optional[str]] = mapped_column(String(200))
    addr2: Mapped[Optional[str]] = mapped_column(String(200))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    zipcode: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[Optional[str]] = mapped_column(String(50))
    comments: Mapped[Optional[str]] = mapped_column(String(500))
    telegram_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.now())

    # Relationships
    sales: Mapped[List["Sales"]] = relationship(back_populates="customer")
    activities: Mapped[List["Activity"]] = relationship(back_populates="customer")


# ── Product ───────────────────────────────────────────────────────────

class Product(Base):
    __tablename__ = "product"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(200))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    type: Mapped[Optional[str]] = mapped_column(String(50))
    version: Mapped[Optional[str]] = mapped_column(String(20))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    start_dt: Mapped[Optional[datetime]] = mapped_column(Date)
    end_dt: Mapped[Optional[datetime]] = mapped_column(Date)
    comments: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.now())

    # Relationships
    sales: Mapped[List["Sales"]] = relationship(back_populates="product")
    activities: Mapped[List["Activity"]] = relationship(back_populates="product")


# ── Sales ─────────────────────────────────────────────────────────────

class Sales(Base):
    __tablename__ = "sales"

    sales_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customer.customer_id"))
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("product.product_id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    sale_date: Mapped[Optional[datetime]] = mapped_column(Date)
    total_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    comments: Mapped[Optional[str]] = mapped_column(String(500))

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="sales")
    product: Mapped["Product"] = relationship(back_populates="sales")


# ── Activity ──────────────────────────────────────────────────────────

class Activity(Base):
    __tablename__ = "activity"

    activity_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customer.customer_id"))
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("product.product_id"))
    sales_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sales.sales_id"))
    activity_type: Mapped[Optional[str]] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    comments: Mapped[Optional[str]] = mapped_column(String(500))
    activity_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=func.now())
    session_id: Mapped[Optional[str]] = mapped_column(String(100))
    url_data: Mapped[Optional[str]] = mapped_column(String(1000))

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="activities")
    product: Mapped[Optional["Product"]] = relationship(back_populates="activities")
