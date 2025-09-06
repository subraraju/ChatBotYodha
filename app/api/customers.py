from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_database
from app.models.database_models import Customer
from app.models.pydantic_models import CustomerResponse

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("/", response_model=List[CustomerResponse])
def get_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_database)):
    """Get all customers with pagination"""
    customers = db.query(Customer).offset(skip).limit(limit).all()
    return customers


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_database)):
    """Get a specific customer by ID"""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/email/{email}", response_model=CustomerResponse)
def get_customer_by_email(email: str, db: Session = Depends(get_database)):
    """Get a customer by email address"""
    customer = db.query(Customer).filter(Customer.email == email).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/search/{search_term}")
def search_customers(search_term: str, db: Session = Depends(get_database)):
    """Search customers by name, email, or phone"""
    customers = (
        db.query(Customer)
        .filter(
            (Customer.first_name.ilike(f"%{search_term}%"))
            | (Customer.last_name.ilike(f"%{search_term}%"))
            | (Customer.email.ilike(f"%{search_term}%"))
            | (Customer.phone.ilike(f"%{search_term}%"))
        )
        .all()
    )
    return customers
