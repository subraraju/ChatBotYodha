"""
Customer / Product / Sales — read-only CRUD endpoints for the admin panel.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, Product, Sales
from app.schemas import CustomerOut, ProductOut, SaleOut, MarketingPersonOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data", tags=["Data"])


@router.get("/customers", response_model=List[CustomerOut])
def list_customers(
    party_type: str = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(Customer).limit(limit)
    if party_type:
        stmt = stmt.where(Customer.party_type == party_type)
    return db.execute(stmt).scalars().all()


@router.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    row = db.get(Customer, customer_id)
    if not row:
        from fastapi import HTTPException
        raise HTTPException(404, "Customer not found")
    return row


@router.get("/products", response_model=List[ProductOut])
def list_products(limit: int = Query(50, le=200), db: Session = Depends(get_db)):
    return db.execute(select(Product).limit(limit)).scalars().all()


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    row = db.get(Product, product_id)
    if not row:
        from fastapi import HTTPException
        raise HTTPException(404, "Product not found")
    return row


@router.get("/sales", response_model=List[SaleOut])
def list_sales(
    customer_id: int = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(Sales).limit(limit)
    if customer_id:
        stmt = stmt.where(Sales.customer_id == customer_id)
    return db.execute(stmt).scalars().all()


@router.get("/marketing-persons", response_model=List[MarketingPersonOut])
def list_marketing_persons(db: Session = Depends(get_db)):
    stmt = select(Customer).where(Customer.party_type == "MKTG")
    return db.execute(stmt).scalars().all()
