from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_database
from app.models.database_models import Sales, Customer, Product
from app.models.pydantic_models import SalesResponse

router = APIRouter(prefix="/api/sales", tags=["sales"])


@router.get("/", response_model=List[SalesResponse])
def get_sales(
    skip: int = 0,
    limit: int = 100,
    customer_id: int = None,
    product_id: int = None,
    db: Session = Depends(get_database),
):
    """Get all sales with optional filtering"""
    query = db.query(Sales)
    if customer_id:
        query = query.filter(Sales.customer_id == customer_id)
    if product_id:
        query = query.filter(Sales.product_id == product_id)
    sales = query.offset(skip).limit(limit).all()
    return sales


@router.get("/{sale_id}", response_model=SalesResponse)
def get_sale(sale_id: int, db: Session = Depends(get_database)):
    """Get a specific sale by ID"""
    sale = db.query(Sales).filter(Sales.sale_id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale


@router.get("/customer/{customer_id}")
def get_sales_by_customer(customer_id: int, db: Session = Depends(get_database)):
    """Get all sales for a specific customer"""
    sales = db.query(Sales).filter(Sales.customer_id == customer_id).all()
    return sales


@router.get("/product/{product_id}")
def get_sales_by_product(product_id: int, db: Session = Depends(get_database)):
    """Get all sales for a specific product"""
    sales = db.query(Sales).filter(Sales.product_id == product_id).all()
    return sales


@router.get("/analytics/summary")
def get_sales_summary(db: Session = Depends(get_database)):
    """Get sales analytics summary"""
    from sqlalchemy import func

    total_sales = db.query(func.sum(Sales.total_amount)).scalar() or 0
    total_quantity = db.query(func.sum(Sales.quantity)).scalar() or 0
    sales_count = db.query(func.count(Sales.sale_id)).scalar() or 0

    top_customers = (
        db.query(
            Customer.first_name,
            Customer.last_name,
            Customer.email,
            func.sum(Sales.total_amount).label("total_spent"),
        )
        .join(Sales)
        .group_by(
            Customer.customer_id,
            Customer.first_name,
            Customer.last_name,
            Customer.email,
        )
        .order_by(func.sum(Sales.total_amount).desc())
        .limit(5)
        .all()
    )

    top_products = (
        db.query(
            Product.product_name,
            func.sum(Sales.quantity).label("total_sold"),
            func.sum(Sales.total_amount).label("total_revenue"),
        )
        .join(Sales)
        .group_by(Product.product_id, Product.product_name)
        .order_by(func.sum(Sales.total_amount).desc())
        .limit(5)
        .all()
    )

    return {
        "total_sales": float(total_sales),
        "total_quantity": int(total_quantity),
        "sales_count": int(sales_count),
        "top_customers": [
            {
                "name": f"{customer.first_name} {customer.last_name}",
                "email": customer.email,
                "total_spent": float(customer.total_spent),
            }
            for customer in top_customers
        ],
        "top_products": [
            {
                "product_name": product.product_name,
                "total_sold": int(product.total_sold),
                "total_revenue": float(product.total_revenue),
            }
            for product in top_products
        ],
    }
