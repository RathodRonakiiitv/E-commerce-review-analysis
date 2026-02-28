"""Scraping endpoints for initiating and monitoring scrape jobs."""
import asyncio
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from typing import Dict
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.scraping import ScrapeRequest, ScrapeStatusResponse, JobStatus

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Thread pool for running Playwright (needs ProactorEventLoop on Windows)
_scrape_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="scraper")

# In-memory job storage (in production, use Redis)
scrape_jobs: Dict[str, dict] = {}

# Maximum completed jobs to keep in memory
_MAX_COMPLETED_JOBS = 200


def _cleanup_old_jobs():
    """Remove oldest completed/failed jobs when storage exceeds limit."""
    finished = [
        (k, v) for k, v in scrape_jobs.items()
        if v["status"] in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)
    ]
    if len(finished) > _MAX_COMPLETED_JOBS:
        # Sort by completion time, remove oldest
        finished.sort(key=lambda kv: kv[1].get("completed_at") or datetime.min)
        for k, _ in finished[: len(finished) - _MAX_COMPLETED_JOBS]:
            del scrape_jobs[k]


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
    
    try:
        scrape_jobs[job_id]["status"] = JobStatus.RUNNING
        scrape_jobs[job_id]["started_at"] = datetime.now(timezone.utc)
        
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
        
        if reviews_count == 0:
            scrape_jobs[job_id]["status"] = JobStatus.FAILED
            scrape_jobs[job_id]["error"] = "Scraper collected 0 reviews. The product may have no reviews or Flipkart blocked the request. Try again."
            scrape_jobs[job_id]["completed_at"] = datetime.now(timezone.utc)
        else:
            scrape_jobs[job_id]["status"] = JobStatus.COMPLETED
            scrape_jobs[job_id]["product_id"] = product_id
            scrape_jobs[job_id]["reviews_scraped"] = reviews_count
            scrape_jobs[job_id]["progress"] = 100
            scrape_jobs[job_id]["completed_at"] = datetime.now(timezone.utc)
            scrape_jobs[job_id]["message"] = f"Successfully scraped {reviews_count} reviews"
        
    except Exception as e:
        scrape_jobs[job_id]["status"] = JobStatus.FAILED
        scrape_jobs[job_id]["error"] = str(e)
        scrape_jobs[job_id]["completed_at"] = datetime.now(timezone.utc)


def update_job_progress(job_id: str, progress: int, reviews_count: int):
    """Update job progress."""
    if job_id in scrape_jobs:
        scrape_jobs[job_id]["progress"] = progress
        scrape_jobs[job_id]["reviews_scraped"] = reviews_count


@router.post("", response_model=ScrapeStatusResponse)
@limiter.limit("5/minute")
async def start_scraping(
    request: Request,
    body: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """Start scraping a product from URL."""
    try:
        platform = detect_platform(body.url)
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
    
    # Cleanup old jobs to prevent memory leak
    _cleanup_old_jobs()

    # Add background task
    background_tasks.add_task(run_scrape_job, job_id, body.url, body.max_reviews)
    
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
    job["completed_at"] = datetime.now(timezone.utc)
    job["message"] = "Job cancelled by user"
    
    return {"message": "Job cancelled"}
