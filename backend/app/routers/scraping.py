"""Scraping endpoints for initiating and monitoring scrape jobs."""
import asyncio
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends
from typing import Dict, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models.job import ScrapeJob
from app.schemas.scraping import ScrapeRequest, ScrapeStatusResponse, JobStatus

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Thread pool for running Playwright (needs ProactorEventLoop on Windows)
_scrape_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="scraper")

# Maximum completed jobs to keep in database
_MAX_COMPLETED_JOBS = 200


def _cleanup_old_jobs(db: Session):
    """Remove oldest completed/failed jobs when storage exceeds limit."""
    finished_count = db.query(ScrapeJob).filter(
        ScrapeJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED])
    ).count()

    if finished_count > _MAX_COMPLETED_JOBS:
        # Find oldest jobs to delete
        old_jobs = db.query(ScrapeJob).filter(
            ScrapeJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED])
        ).order_by(ScrapeJob.completed_at.asc()).limit(finished_count - _MAX_COMPLETED_JOBS).all()
        
        for job in old_jobs:
            db.delete(job)
        db.commit()


def detect_platform(url: str) -> str:
    """Detect e-commerce platform from URL. Only Flipkart is supported."""
    url_lower = url.lower()
    if "flipkart" in url_lower:
        return "flipkart"
    else:
        raise ValueError("Unsupported platform. Only Flipkart product URLs are supported.")


async def run_scrape_job(job_id: str, url: str, max_reviews: int):
    """Background task to run scraping job."""
    from app.services.scraper import scrape_product
    
    db = SessionLocal()
    try:
        job = db.query(ScrapeJob).filter(ScrapeJob.job_id == job_id).first()
        if not job:
            return

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        
        # Playwright needs ProactorEventLoop for subprocess support on Windows.
        # uvicorn's event loop doesn't support it, so we run the scraper
        # in a dedicated thread with its own ProactorEventLoop.
        def _scrape_in_thread():
            if sys.platform == "win32":
                loop = asyncio.ProactorEventLoop()
            else:
                loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    scrape_product(
                        url=url,
                        max_reviews=max_reviews,
                        progress_callback=lambda p, c: update_job_progress(job_id, p, c),
                    )
                )
            finally:
                loop.close()

        main_loop = asyncio.get_event_loop()
        product_id, reviews_count = await main_loop.run_in_executor(
            _scrape_pool, _scrape_in_thread
        )
        
        # Re-fetch job to update it
        job = db.query(ScrapeJob).filter(ScrapeJob.job_id == job_id).first()
        if reviews_count == 0:
            job.status = JobStatus.FAILED
            job.error = "Scraper collected 0 reviews. The product may have no reviews or Flipkart blocked the request. Try again."
        else:
            job.status = JobStatus.COMPLETED
            job.product_id = product_id
            job.reviews_scraped = reviews_count
            job.progress = 100
            job.message = f"Successfully scraped {reviews_count} reviews"
        
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        
    except Exception as e:
        error_text = str(e)
        if "Timeout" in error_text or "timeout" in error_text:
            error_text = (
                "Flipkart took too long to respond. Please try again in a minute "
                "or reduce the review count to 50."
            )
        
        # Re-fetch job to update it
        job = db.query(ScrapeJob).filter(ScrapeJob.job_id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            job.error = error_text
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


def update_job_progress(job_id: str, progress: int, reviews_count: int):
    """Update job progress in database."""
    db = SessionLocal()
    try:
        job = db.query(ScrapeJob).filter(ScrapeJob.job_id == job_id).first()
        if job:
            job.progress = progress
            job.reviews_scraped = reviews_count
            db.commit()
    finally:
        db.close()


@router.post("", response_model=ScrapeStatusResponse)
@limiter.limit("5/minute")
async def start_scraping(
    request: Request,
    body: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start scraping a product from URL."""
    try:
        platform = detect_platform(body.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create job in database
    job_id = str(uuid.uuid4())
    job = ScrapeJob(
        job_id=job_id,
        status=JobStatus.PENDING,
        message=f"Scraping {platform} product...",
        progress=0,
        reviews_scraped=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Cleanup old jobs to prevent database bloat
    _cleanup_old_jobs(db)

    # Add background task
    background_tasks.add_task(run_scrape_job, job_id, body.url, body.max_reviews)
    
    return ScrapeStatusResponse(
        job_id=job.job_id,
        status=job.status,
        product_id=job.product_id,
        progress=job.progress,
        reviews_scraped=job.reviews_scraped,
        message=job.message,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error=job.error
    )


@router.get("/{job_id}/status", response_model=ScrapeStatusResponse)
async def get_scrape_status(job_id: str, db: Session = Depends(get_db)):
    """Get the status of a scraping job."""
    job = db.query(ScrapeJob).filter(ScrapeJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return ScrapeStatusResponse(
        job_id=job.job_id,
        status=job.status,
        product_id=job.product_id,
        progress=job.progress,
        reviews_scraped=job.reviews_scraped,
        message=job.message,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error=job.error
    )


@router.delete("/{job_id}")
async def cancel_scrape(job_id: str, db: Session = Depends(get_db)):
    """Cancel a running scrape job."""
    job = db.query(ScrapeJob).filter(ScrapeJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Job already finished")
    
    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.now(timezone.utc)
    job.message = "Job cancelled by user"
    db.commit()
    
    return {"message": "Job cancelled"}
