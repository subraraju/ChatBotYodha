from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_database
from app.models.database_models import Activity, Customer, Product
from app.models.pydantic_models import ActivityResponse

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("/", response_model=List[ActivityResponse])
def get_activities(
    skip: int = 0,
    limit: int = 100,
    customer_id: int = None,
    product_id: int = None,
    activity_type: str = None,
    db: Session = Depends(get_database),
):
    """Get all activities with optional filtering"""
    query = db.query(Activity)
    if customer_id:
        query = query.filter(Activity.customer_id == customer_id)
    if product_id:
        query = query.filter(Activity.product_id == product_id)
    if activity_type:
        query = query.filter(Activity.activity_type == activity_type)
    activities = (
        query.order_by(Activity.activity_date.desc()).offset(skip).limit(limit).all()
    )
    return activities


@router.get("/{activity_id}", response_model=ActivityResponse)
def get_activity(activity_id: int, db: Session = Depends(get_database)):
    """Get a specific activity by ID"""
    activity = db.query(Activity).filter(Activity.activity_id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.get("/customer/{customer_id}")
def get_activities_by_customer(customer_id: int, db: Session = Depends(get_database)):
    """Get all activities for a specific customer"""
    activities = (
        db.query(Activity)
        .filter(Activity.customer_id == customer_id)
        .order_by(Activity.activity_date.desc())
        .all()
    )
    return activities


@router.get("/product/{product_id}")
def get_activities_by_product(product_id: int, db: Session = Depends(get_database)):
    """Get all activities for a specific product"""
    activities = (
        db.query(Activity)
        .filter(Activity.product_id == product_id)
        .order_by(Activity.activity_date.desc())
        .all()
    )
    return activities


@router.get("/types/list")
def get_activity_types(db: Session = Depends(get_database)):
    """Get list of all unique activity types"""
    from sqlalchemy import distinct

    types = (
        db.query(distinct(Activity.activity_type))
        .filter(Activity.activity_type.isnot(None))
        .all()
    )
    return [type_[0] for type_ in types]


@router.get("/recent/{days}")
def get_recent_activities(days: int = 7, db: Session = Depends(get_database)):
    """Get activities from the last N days"""
    from datetime import datetime, timedelta
    from sqlalchemy import and_

    start_date = datetime.now() - timedelta(days=days)
    activities = (
        db.query(Activity)
        .filter(Activity.activity_date >= start_date)
        .order_by(Activity.activity_date.desc())
        .all()
    )
    return activities
