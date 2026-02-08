"""Product management endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Review
from app.schemas.product import ProductResponse, ProductListResponse
from app.schemas.review import ReviewResponse, ReviewListResponse
import math

router = APIRouter()


@router.get("", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """List all analyzed products with pagination."""
    total = db.query(Product).count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    products = (
        db.query(Product)
        .order_by(Product.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    return ProductListResponse(
        items=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product and all its reviews."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": f"Product {product_id} deleted successfully"}


@router.get("/{product_id}/reviews", response_model=ReviewListResponse)
async def get_product_reviews(
    product_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sentiment: Optional[str] = Query(None, pattern="^(positive|negative|neutral)$"),
    rating: Optional[int] = Query(None, ge=1, le=5),
    verified_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get reviews for a product with filtering and pagination."""
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Build query with filters
    query = db.query(Review).filter(Review.product_id == product_id)
    
    if sentiment:
        query = query.filter(Review.sentiment_label == sentiment)
    if rating:
        query = query.filter(Review.rating == rating)
    if verified_only:
        query = query.filter(Review.verified_purchase.is_(True))
    
    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    reviews = (
        query
        .order_by(Review.scraped_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    return ReviewListResponse(
        items=[ReviewResponse.model_validate(r) for r in reviews],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
