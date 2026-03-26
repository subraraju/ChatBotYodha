"""
Customer look-up helpers — search by email / phone / name,
fetch purchases with pagination.

All queries go through SQLAlchemy (no raw psycopg2).
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from app.models import Customer, Sales, Product

logger = logging.getLogger(__name__)

PAGE_SIZE = 5  # purchases shown per page


# ── Look up customer ──────────────────────────────────────────────────

def find_customer(
    db: Session,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Return customer dict or None.
    Priority: email → phone → name (first+last ilike).
    """
    stmt = select(Customer)

    if email:
        stmt = stmt.where(Customer.email.ilike(email.strip()))
    elif phone:
        clean = phone.strip().replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        # Use regexp_replace to strip non-digits from DB value for comparison
        stmt = stmt.where(
            func.regexp_replace(Customer.phone, r'[^0-9]', '', 'g').ilike(f"%{clean[-10:]}%")
        )
    elif name:
        parts = name.strip().split()
        first = parts[0] if parts else ""
        last = parts[-1] if len(parts) > 1 else ""
        if first:
            stmt = stmt.where(Customer.first_name.ilike(f"%{first}%"))
        if last and last != first:
            stmt = stmt.where(Customer.last_name.ilike(f"%{last}%"))
    else:
        return None

    row = db.execute(stmt).scalars().first()
    if not row:
        return None

    return {
        "customer_id": row.customer_id,
        "first_name": row.first_name,
        "last_name": row.last_name,
        "email": row.email,
        "phone": row.phone,
        "party_type": row.party_type,
        "city": row.city,
        "state": row.state,
    }


# ── Purchases ─────────────────────────────────────────────────────────

def get_purchases(
    db: Session,
    customer_id: int,
    offset: int = 0,
    limit: int = PAGE_SIZE,
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Return (purchases_list, has_more).
    Each purchase is a dict with product + sale info.
    """
    total = db.scalar(
        select(func.count()).select_from(Sales).where(Sales.customer_id == customer_id)
    ) or 0

    rows = (
        db.execute(
            select(Sales, Product)
            .join(Product, Sales.product_id == Product.product_id)
            .where(Sales.customer_id == customer_id)
            .order_by(Sales.sale_date.desc())
            .offset(offset)
            .limit(limit)
        )
        .all()
    )

    purchases = []
    for sale, product in rows:
        purchases.append(
            {
                "sale_id": sale.sales_id,
                "product_id": product.product_id,
                "product_name": product.product_name,
                "category": product.category or "",
                "type": product.type or "",
                "version": product.version or "",
                "price": float(product.price) if product.price else 0,
                "quantity": sale.quantity,
                "sale_date": str(sale.sale_date) if sale.sale_date else "",
                "total_amount": float(sale.total_amount) if sale.total_amount else 0,
            }
        )

    has_more = (offset + limit) < total
    return purchases, has_more


# ── Marketing persons ─────────────────────────────────────────────────

def get_marketing_persons(
    db: Session,
    party_type: str = "MKTG",
) -> List[Dict[str, Any]]:
    """Return list of marketing-person dicts from customer table."""
    rows = (
        db.execute(
            select(Customer).where(Customer.party_type == party_type)
        )
        .scalars()
        .all()
    )
    return [
        {
            "customer_id": r.customer_id,
            "first_name": r.first_name,
            "last_name": r.last_name,
            "email": r.email,
            "phone": r.phone,
        }
        for r in rows
    ]


def get_marketing_person_by_id(
    db: Session, person_id: int
) -> Optional[Dict[str, Any]]:
    """Return single marketing person dict or None."""
    row = db.get(Customer, person_id)
    if not row or row.party_type != "MKTG":
        return None
    return {
        "customer_id": row.customer_id,
        "first_name": row.first_name,
        "last_name": row.last_name,
        "email": row.email,
        "phone": row.phone,
    }
