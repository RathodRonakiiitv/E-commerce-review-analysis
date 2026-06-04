"""Model for tracking background scraping jobs."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base


class ScrapeJob(Base):
    """Tracks the status of a background scraping task."""
    
    __tablename__ = "scrape_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), unique=True, index=True, nullable=False)
    status = Column(String(20), default="pending")  # pending, running, completed, failed, cancelled
    
    product_id = Column(Integer, nullable=True)
    progress = Column(Integer, default=0)
    reviews_scraped = Column(Integer, default=0)
    
    message = Column(String(255), nullable=True)
    error = Column(Text, nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ScrapeJob(job_id='{self.job_id}', status='{self.status}')>"
