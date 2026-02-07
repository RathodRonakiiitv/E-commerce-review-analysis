"""Analysis runner - orchestrates all analysis services."""
from datetime import datetime

from app.database import SessionLocal
from app.models import Product


async def run_complete_analysis(product_id: int):
    """
    Run complete analysis pipeline for a product.
    
    This includes:
    1. Sentiment analysis
    2. Aspect-based sentiment
    3. Topic modeling
    4. Fake review detection
    """
    db = SessionLocal()
    
    try:
        # Import services
        from app.services.analysis.sentiment import analyze_product_sentiment
        from app.services.analysis.aspects import analyze_product_aspects
        from app.services.analysis.topics import analyze_product_topics
        from app.services.analysis.fake_detection import detect_fake_reviews
        from app.services.analysis.insights import generate_product_insights
        
        print(f"[ANALYSIS] Starting analysis for product {product_id}")
        
        # 1. Sentiment Analysis
        print("  > Running sentiment analysis...")
        await analyze_product_sentiment(db, product_id)
        
        # 2. Fake Review Detection (needs sentiment first)
        print("  > Detecting fake reviews...")
        await detect_fake_reviews(db, product_id)
        
        # 3. Aspect-Based Sentiment
        print("  > Analyzing aspects...")
        await analyze_product_aspects(db, product_id)
        
        # 4. Topic Modeling
        print("  > Modeling topics...")
        await analyze_product_topics(db, product_id)
        
        # 5. Generate Insights (aggregates everything)
        print("  > Generating insights...")
        await generate_product_insights(db, product_id)
        
        # Update product timestamp
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.last_analyzed = datetime.utcnow()
            db.commit()
        
        print(f"[DONE] Analysis complete for product {product_id}")
        
    except Exception as e:
        print(f"[ERROR] Analysis error for product {product_id}: {e}")
        raise
    
    finally:
        db.close()
