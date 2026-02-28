"""Analysis runner - orchestrates all analysis services."""
import logging
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models import Product

logger = logging.getLogger(__name__)


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
        
        logger.info("Starting analysis for product %d", product_id)
        completed_steps: list[str] = []
        failed_steps: list[str] = []
        
        # 1. Sentiment Analysis (required — other steps depend on it)
        logger.info("  Running sentiment analysis...")
        await analyze_product_sentiment(db, product_id)
        completed_steps.append("sentiment")
        
        # 2-4 are independent — run each, log failures, continue
        for step_name, step_fn in [
            ("fake_detection", lambda: detect_fake_reviews(db, product_id)),
            ("aspects", lambda: analyze_product_aspects(db, product_id)),
            ("topics", lambda: analyze_product_topics(db, product_id)),
        ]:
            try:
                logger.info("  Running %s...", step_name)
                await step_fn()
                completed_steps.append(step_name)
            except Exception as e:
                logger.error("  %s failed (non-fatal): %s", step_name, e)
                failed_steps.append(step_name)
        
        # 5. Generate Insights (aggregates everything available)
        try:
            logger.info("  Generating insights...")
            await generate_product_insights(db, product_id)
            completed_steps.append("insights")
        except Exception as e:
            logger.error("  insights failed (non-fatal): %s", e)
            failed_steps.append("insights")
        
        # Update product timestamp
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.last_analyzed = datetime.now(timezone.utc)
            db.commit()
        
        if failed_steps:
            logger.warning(
                "Analysis partially complete for product %d — OK: %s | FAILED: %s",
                product_id, completed_steps, failed_steps,
            )
        else:
            logger.info("Analysis complete for product %d", product_id)
        
    except Exception as e:
        logger.error("Analysis error for product %d: %s", product_id, e)
        raise
    
    finally:
        db.close()
