"""FastAPI Application Entry Point."""
import sys
import io

# Force UTF-8 encoding for stdout/stderr on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import products, scraping, analysis, comparison, export, ai, demo


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("[START] Starting E-commerce Review Analyzer API...")
    init_db()
    print("[OK] Database tables initialized")
    
    # Pre-load ML models (lazy loading on first use)
    print("[OK] ML models will be loaded on first request")
    print("[OK] Groq AI integration ready")
    
    yield
    
    # Shutdown
    print("[STOP] Shutting down API...")


app = FastAPI(
    title="E-commerce Product Review Analyzer",
    description="""
    Analyze product reviews from Amazon and Flipkart with AI-powered insights.
    
    ## Features
    - Scrape reviews from product URLs
    - Sentiment Analysis - Positive/Negative/Neutral classification
    - Aspect-Based Sentiment - Quality, Price, Delivery, etc.
    - Topic Modeling - Discover what customers talk about
    - Fake Review Detection - Flag suspicious reviews
    - Comparison - Compare multiple products
    - Export - PDF and CSV reports
    - AI Insights - Groq-powered summaries and suggestions
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
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
    return {"status": "healthy", "message": "E-commerce Review Analyzer API is running"}


@app.get("/api/stats", tags=["Health"])
async def get_stats():
    """Get system statistics."""
    from app.database import SessionLocal
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
