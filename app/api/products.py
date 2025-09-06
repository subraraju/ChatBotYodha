from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_database
from app.models.database_models import Product
from app.models.pydantic_models import ProductResponse

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/", response_model=List[ProductResponse])
def get_products(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    db: Session = Depends(get_database),
):
    """Get all products with optional filtering by category"""
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    products = query.offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_database)):
    """Get a specific product by ID"""
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/search/{search_term}")
def search_products(search_term: str, db: Session = Depends(get_database)):
    """Search products by name, category, or type"""
    products = (
        db.query(Product)
        .filter(
            (Product.product_name.ilike(f"%{search_term}%"))
            | (Product.category.ilike(f"%{search_term}%"))
            | (Product.type.ilike(f"%{search_term}%"))
        )
        .all()
    )
    return products


@router.get("/category/{category}")
def get_products_by_category(category: str, db: Session = Depends(get_database)):
    """Get all products in a specific category"""
    products = db.query(Product).filter(Product.category == category).all()
    return products
