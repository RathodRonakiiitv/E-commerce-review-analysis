"""FastAPI Application Entry Point."""
import logging
import sys
import io
import os
import asyncio

# Playwright needs ProactorEventLoop on Windows to spawn browser subprocesses.
# Must be set BEFORE uvicorn creates its event loop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Force UTF-8 encoding for stdout/stderr on Windows (skip during testing)
if sys.platform == "win32" and "pytest" not in sys.modules:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.database import init_db
from app.routers import products, scraping, analysis, comparison, export, ai, demo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Rate limiter (default: 60 requests/minute per IP)
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Flipkart Review Analyzer API...")
    init_db()
    logger.info("Database tables initialized")
    
    # Cleanup stale jobs (any job in running/pending state after restart is dead)
    from app.database import SessionLocal
    from app.models.job import ScrapeJob
    from app.schemas.scraping import JobStatus
    from datetime import datetime, timezone
    
    db = SessionLocal()
    try:
        stale_jobs = db.query(ScrapeJob).filter(
            ScrapeJob.status.in_([JobStatus.RUNNING, JobStatus.PENDING])
        ).all()
        if stale_jobs:
            logger.info("Cleaning up %d stale scraping jobs", len(stale_jobs))
            for job in stale_jobs:
                job.status = JobStatus.FAILED
                job.error = "Server restarted during analysis. Please try again."
                job.completed_at = datetime.now(timezone.utc)
            db.commit()
    except Exception as e:
        logger.error("Failed to cleanup stale jobs: %s", e)
    finally:
        db.close()
    
    # Pre-load ML models (lazy loading on first use)
    logger.info("ML models will be loaded on first request")
    logger.info("Groq AI integration ready")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API...")


app = FastAPI(
    title="Flipkart Product Review Analyzer",
    description="""
    Analyze Flipkart product reviews with AI-powered insights.
    
    ## Features
    - Scrape reviews from Flipkart product URLs
    - Sentiment Analysis - Positive/Negative/Neutral classification
    - Aspect-Based Sentiment - Quality, Price, Delivery, etc.
    - Topic Modeling - Discover what customers talk about
    - Fake Review Detection - Flag suspicious reviews
    - Comparison - Compare multiple products
    - Export - PDF and CSV reports
    - AI Insights - Groq-powered summaries and suggestions
    """,
    version="2.0.0",
    lifespan=lifespan
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(scraping.router, prefix="/api/scrape", tags=["Scraping"])
app.include_router(analysis.router, prefix="/api/products", tags=["Analysis"])
app.include_router(comparison.router, prefix="/api/compare", tags=["Comparison"])
app.include_router(export.router, prefix="/api/products", tags=["Export"])
app.include_router(ai.router, prefix="/api", tags=["AI Insights"])
app.include_router(demo.router, prefix="/api", tags=["Demo"])


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Check if API is running."""
    return {"status": "healthy", "message": "Flipkart Review Analyzer API is running"}


@app.get("/api/stats", tags=["Health"])
async def get_stats():
    """Get system statistics."""
    from fastapi import Depends
    from app.database import SessionLocal, get_db
    from app.models import Product, Review
    
    db = SessionLocal()
    try:
        total_products = db.query(Product).count()
        total_reviews = db.query(Review).count()
        analyzed_reviews = db.query(Review).filter(Review.sentiment_label.isnot(None)).count()
        
        return {
            "total_products": total_products,
            "total_reviews": total_reviews,
            "analyzed_reviews": analyzed_reviews,
            "pending_analysis": total_reviews - analyzed_reviews
        }
    finally:
        db.close()
