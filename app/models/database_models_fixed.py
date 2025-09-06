from sqlalchemy import Integer, String, DateTime, Date, Text, ForeignKey, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from decimal import Decimal
from typing import Optional


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customer"

    customer_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(String(500))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    zip_code: Mapped[Optional[str]] = mapped_column(String(10))
    registration_date: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp()
    )

    # Relationships
    sales: Mapped[list["Sales"]] = relationship("Sales", back_populates="customer")
    activities: Mapped[list["Activity"]] = relationship(
        "Activity", back_populates="customer"
    )


class Product(Base):
    __tablename__ = "product"

    product_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    product_name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    model_number: Mapped[Optional[str]] = mapped_column(String(100))
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    dimensions: Mapped[Optional[str]] = mapped_column(String(100))
    color: Mapped[Optional[str]] = mapped_column(String(50))
    warranty_period: Mapped[Optional[str]] = mapped_column(String(100))
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    sales: Mapped[list["Sales"]] = relationship("Sales", back_populates="product")
    activities: Mapped[list["Activity"]] = relationship(
        "Activity", back_populates="product"
    )


class Sales(Base):
    __tablename__ = "sales"

    sales_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customer.customer_id")
    )
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("product.product_id"))
    quantity: Mapped[int] = mapped_column(Integer)
    sale_date: Mapped[datetime] = mapped_column(Date)
    comments: Mapped[Optional[str]] = mapped_column(String)
    total_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="sales")
    product: Mapped["Product"] = relationship("Product", back_populates="sales")


class Activity(Base):
    __tablename__ = "activity"

    activity_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customer.customer_id")
    )
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("product.product_id"))
    sales_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sales.sales_id"))
    activity_type: Mapped[Optional[str]] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    comments: Mapped[Optional[str]] = mapped_column(String(200))
    activity_date: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp()
    )
    session_id: Mapped[Optional[str]] = mapped_column(String(50))
    url_data: Mapped[Optional[str]] = mapped_column(String(1000))

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="activities")
    product: Mapped["Product"] = relationship("Product", back_populates="activities")
    sales: Mapped[Optional["Sales"]] = relationship("Sales", foreign_keys=[sales_id])
