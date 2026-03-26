"""
Activity tracking — CRUD for the activity table.

Records CHATBOT sessions, product interactions, meeting bookings, etc.
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Activity, Sales

logger = logging.getLogger(__name__)


def get_latest_sales_id(
    db: Session, customer_id: int, product_id: Optional[int] = None
) -> Optional[int]:
    """Most-recent sale_id for a customer (optionally filtered by product)."""
    stmt = (
        select(Sales.sale_id)
        .where(Sales.customer_id == customer_id)
        .order_by(Sales.sale_date.desc())
        .limit(1)
    )
    if product_id:
        stmt = stmt.where(Sales.product_id == product_id)
    return db.scalar(stmt)


def create_chatbot_activity(
    db: Session,
    customer_id: int,
    session_id: str,
    url_data: Optional[str] = None,
    product_id: Optional[int] = None,
    description: Optional[str] = None,
    comments: Optional[str] = None,
) -> Optional[int]:
    """
    Insert an activity of type CHATBOT.
    Returns activity_id or None on failure.
    """
    sales_id = get_latest_sales_id(db, customer_id, product_id) if product_id else None

    activity = Activity(
        customer_id=customer_id,
        product_id=product_id,
        sales_id=sales_id,
        activity_type="CHATBOT",
        description=description or "Customer chatbot session",
        comments=comments,
        session_id=session_id,
        url_data=url_data,
    )
    try:
        db.add(activity)
        db.commit()
        db.refresh(activity)
        logger.info(
            "Created activity %d (customer=%d, session=%s)",
            activity.activity_id,
            customer_id,
            session_id,
        )
        return activity.activity_id
    except Exception as exc:
        db.rollback()
        logger.error("Failed to create activity: %s", exc)
        return None


def update_activity_summary(
    db: Session,
    activity_id: int,
    summary: str,
    comments: Optional[str] = None,
) -> bool:
    """Append conversation summary to an existing activity."""
    activity = db.get(Activity, activity_id)
    if not activity:
        return False
    activity.description = summary
    if comments:
        activity.comments = comments
    try:
        db.commit()
        return True
    except Exception as exc:
        db.rollback()
        logger.error("Failed to update activity %d: %s", activity_id, exc)
        return False
