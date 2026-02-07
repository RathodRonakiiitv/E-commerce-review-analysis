"""Scraping endpoints for initiating and monitoring scrape jobs."""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict

from app.schemas.scraping import ScrapeRequest, ScrapeStatusResponse, JobStatus

router = APIRouter()

# In-memory job storage (in production, use Redis)
scrape_jobs: Dict[str, dict] = {}


def detect_platform(url: str) -> str:
    """Detect e-commerce platform from URL."""
    url_lower = url.lower()
    if "amazon" in url_lower:
        return "amazon"
    elif "flipkart" in url_lower:
        return "flipkart"
    else:
        raise ValueError("Unsupported platform. Only Amazon and Flipkart are supported.")


async def run_scrape_job(job_id: str, url: str, max_reviews: int):
    """Background task to run scraping job."""
    from app.services.scraper import scrape_product
    
    try:
        scrape_jobs[job_id]["status"] = JobStatus.RUNNING
        scrape_jobs[job_id]["started_at"] = datetime.utcnow()
        
        # Run the scraper
        product_id, reviews_count = await scrape_product(
            url=url,
            max_reviews=max_reviews,
            progress_callback=lambda p, c: update_job_progress(job_id, p, c)
        )
        
        scrape_jobs[job_id]["status"] = JobStatus.COMPLETED
        scrape_jobs[job_id]["product_id"] = product_id
        scrape_jobs[job_id]["reviews_scraped"] = reviews_count
        scrape_jobs[job_id]["progress"] = 100
        scrape_jobs[job_id]["completed_at"] = datetime.utcnow()
        scrape_jobs[job_id]["message"] = f"Successfully scraped {reviews_count} reviews"
        
    except Exception as e:
        scrape_jobs[job_id]["status"] = JobStatus.FAILED
        scrape_jobs[job_id]["error"] = str(e)
        scrape_jobs[job_id]["completed_at"] = datetime.utcnow()


def update_job_progress(job_id: str, progress: int, reviews_count: int):
    """Update job progress."""
    if job_id in scrape_jobs:
        scrape_jobs[job_id]["progress"] = progress
        scrape_jobs[job_id]["reviews_scraped"] = reviews_count


@router.post("", response_model=ScrapeStatusResponse)
async def start_scraping(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """Start scraping a product from URL."""
    try:
        platform = detect_platform(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create job
    job_id = str(uuid.uuid4())
    scrape_jobs[job_id] = {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "product_id": None,
        "progress": 0,
        "reviews_scraped": 0,
        "message": f"Scraping {platform} product...",
        "started_at": None,
        "completed_at": None,
        "error": None
    }
    
    # Add background task
    background_tasks.add_task(run_scrape_job, job_id, request.url, request.max_reviews)
    
    return ScrapeStatusResponse(**scrape_jobs[job_id])


@router.get("/{job_id}/status", response_model=ScrapeStatusResponse)
async def get_scrape_status(job_id: str):
    """Get the status of a scraping job."""
    if job_id not in scrape_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return ScrapeStatusResponse(**scrape_jobs[job_id])


@router.delete("/{job_id}")
async def cancel_scrape(job_id: str):
    """Cancel a running scrape job."""
    if job_id not in scrape_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = scrape_jobs[job_id]
    if job["status"] in [JobStatus.COMPLETED, JobStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Job already finished")
    
    job["status"] = JobStatus.CANCELLED
    job["completed_at"] = datetime.utcnow()
    job["message"] = "Job cancelled by user"
    
    return {"message": "Job cancelled"}
