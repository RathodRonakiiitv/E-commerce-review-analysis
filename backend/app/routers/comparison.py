"""Comparison endpoints for comparing multiple products."""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product
from app.schemas.analysis import ComparisonRequest, ComparisonResponse, ProductComparison

router = APIRouter()


@router.post("", response_model=ComparisonResponse)
async def compare_products(
    request: ComparisonRequest,
    db: Session = Depends(get_db)
):
    """Compare 2-3 products side by side."""
    # Verify all products exist
    products = []
    for pid in request.product_ids:
        product = db.query(Product).filter(Product.id == pid).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {pid} not found")
        products.append(product)
    
    # Get analysis for each product
    from app.services.analysis.insights import generate_product_insights
    from app.services.analysis.aspects import analyze_product_aspects
    
    comparisons: List[ProductComparison] = []
    all_aspects = set()
    
    for product in products:
        # Get insights
        insights = await generate_product_insights(db, product.id)
        aspects_data = await analyze_product_aspects(db, product.id)
        
        # Build aspect scores
        aspect_scores = {}
        for aspect in aspects_data.get("aspects", []):
            aspect_name = aspect["aspect_name"]
            aspect_scores[aspect_name] = aspect["average_score"]
            all_aspects.add(aspect_name)
        
        comparisons.append(ProductComparison(
            product_id=product.id,
            product_name=product.name,
            overall_score=insights["overall_score"],
            avg_rating=float(product.avg_rating) if product.avg_rating else 0,
            total_reviews=product.total_reviews,
            aspects=aspect_scores
        ))
    
    # Determine winners
    best_overall = max(comparisons, key=lambda c: c.overall_score).product_id
    
    aspect_winners = {}
    for aspect in all_aspects:
        scores = [(c.product_id, c.aspects.get(aspect, 0)) for c in comparisons]
        if scores:
            winner = max(scores, key=lambda x: x[1])
            aspect_winners[aspect] = winner[0]
    
    return ComparisonResponse(
        products=comparisons,
        best_overall=best_overall,
        aspect_winners=aspect_winners,
        created_at=datetime.utcnow()
    )
