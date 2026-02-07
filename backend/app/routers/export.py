"""Export endpoints for PDF and CSV downloads."""
import io
import csv
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Review

router = APIRouter()


@router.get("/{product_id}/export/csv")
async def export_csv(product_id: int, db: Session = Depends(get_db)):
    """Export all reviews as CSV."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Review ID", "Rating", "Review Text", "Review Date",
        "Reviewer Name", "Verified Purchase", "Helpful Count",
        "Sentiment", "Sentiment Score", "Is Suspicious"
    ])
    
    # Data rows
    for review in reviews:
        writer.writerow([
            review.id,
            review.rating,
            review.review_text,
            review.review_date,
            review.reviewer_name,
            review.verified_purchase,
            review.helpful_count,
            review.sentiment_label,
            float(review.sentiment_score) if review.sentiment_score else None,
            review.is_suspicious
        ])
    
    output.seek(0)
    
    filename = f"reviews_{product_id}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{product_id}/export/pdf")
async def export_pdf(product_id: int, db: Session = Depends(get_db)):
    """Export analysis report as PDF."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get analysis data
    from app.services.analysis.insights import generate_product_insights
    insights = await generate_product_insights(db, product_id)
    
    # Generate PDF
    from app.services.export.pdf_generator import generate_analysis_pdf
    pdf_buffer = generate_analysis_pdf(product, insights)
    
    filename = f"analysis_{product_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
