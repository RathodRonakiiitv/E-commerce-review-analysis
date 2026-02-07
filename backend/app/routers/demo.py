from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models import Product, Review
from app.services.analysis.runner import run_complete_analysis
import random
from datetime import datetime
import uuid
from app.services.scraper.flipkart import FlipkartScraper

router = APIRouter()

@router.post("/demo")
async def create_demo_product(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Create a demo product with generated reviews to test the analysis pipeline.
    """
    # Create a unique demo product
    demo_id = str(uuid.uuid4())[:8]
    product = Product(
        name=f"Demo Headphones {demo_id}",
        # description and price removed as they are not in Product model
        url=f"http://example.com/demo-headphones-{demo_id}",
        platform="Demo"
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Add dummy reviews
    reviews = [
        Review(product_id=product.id, review_text="Amazing sound quality!", rating=5, reviewer_name="Alice", verified_purchase=True, review_date=datetime.now().date()),
        Review(product_id=product.id, review_text="Battery life is average.", rating=3, reviewer_name="Bob", verified_purchase=True, review_date=datetime.now().date()),
        Review(product_id=product.id, review_text="Best headphones I've ever owned.", rating=5, reviewer_name="Charlie", verified_purchase=True, review_date=datetime.now().date()),
        Review(product_id=product.id, review_text="Too expensive for what it is.", rating=2, reviewer_name="David", verified_purchase=False, review_date=datetime.now().date()),
        Review(product_id=product.id, review_text="Comfortable to wear for long hours.", rating=4, reviewer_name="Eve", verified_purchase=True, review_date=datetime.now().date())
    ]
    
    db.add_all(reviews)
    db.commit()
    
    # Trigger analysis in background
    background_tasks.add_task(run_complete_analysis, product.id)
    
    return {
        "message": "Demo product created successfully!",
        "product_id": product.id,
        "frontend_url": f"http://localhost:3000/products/{product.id}"
    }

@router.post("/demo/oneplus")
async def create_oneplus_demo(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Create a specific demo for OnePlus 13R with realistic simulated data.
    """
    # Check if already exists to avoid clutter
    existing = db.query(Product).filter(Product.name.ilike("%OnePlus 13R%")).first()
    if existing:
        # Re-trigger analysis just in case
        background_tasks.add_task(run_complete_analysis, existing.id)
        return {
            "message": "Demo product already exists, re-analyzing.",
            "product_id": existing.id,
            "frontend_url": f"http://localhost:3000/products/{existing.id}"
        }

    product = Product(
        name="OnePlus 13R (Charcoal, 8GB RAM, 128GB Storage)",
        url=f"http://amazon.in/oneplus-13r-demo-{uuid.uuid4()}", # Unique URL
        platform="Amazon"
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Generate 50 realistic reviews
    positive_reviews = [
        "The battery life is insane! Easily lasts a day and a half.",
        "Performance is buttery smooth with the Snapdragon 8 Gen 2. Gaming is a delight.",
        "Camera quality is surprisingly good, especially low light.",
        "Charging speed is mind-blowing. 0 to 100 in 25 mins!",
        "OxygenOS is clean and bloat-free. Love the experience.",
        "Best phone under 40k hands down. Display is gorgeous.",
        "Value for money king. The haptics are also great.",
        "Design looks premium, though the camera bump is huge.",
        "Network reception is solid. 5G speeds are great.",
        "Speakers are loud and clear. Great for media consumption."
    ]
    
    negative_reviews = [
        "Heating issues while gaming for long sessions.",
        "No wireless charging is a bummer at this price point.",
        "Curved screen causes accidental touches sometimes.",
        "Macro camera is useless. Why even include it?",
        "Battery drain issue after the latest update.",
        "Alert slider feels a bit loose compared to previous models.",
        "No official IP rating? That's concerning.",
        "The back glass is a fingerprint magnet.",
        " charger is bulky to carry around.",
        "Customer service experience was poor."
    ]
    
    neutral_reviews = [
        "It's a good phone but not a huge upgrade from 11R.",
        "Decent performance, but camera could be better.",
        "Good daily driver. Nothing extraordinary.",
        "Average battery life. Expected more.",
        "Software is okay but has some bugs."
    ]
    
    reviews = []
    # Add 30 positive
    for _ in range(30):
        reviews.append(Review(
            product_id=product.id,
            review_text=random.choice(positive_reviews) + " " + random.choice(positive_reviews),
            rating=5,
            reviewer_name=f"User{random.randint(1000,9999)}",
            verified_purchase=True,
            review_date=datetime.now().date()
        ))
    
    # Add 10 negative
    for _ in range(10):
        reviews.append(Review(
            product_id=product.id,
            review_text=random.choice(negative_reviews),
            rating=2,
            reviewer_name=f"User{random.randint(1000,9999)}",
            verified_purchase=True,
            review_date=datetime.now().date()
        ))
        
    # Add 10 neutral
    for _ in range(10):
        reviews.append(Review(
            product_id=product.id,
            review_text=random.choice(neutral_reviews),
            rating=3,
            reviewer_name=f"User{random.randint(1000,9999)}",
            verified_purchase=True,
            review_date=datetime.now().date()
        ))
        
    db.add_all(reviews)
    db.commit()
    
    # Update product stats
    product.total_reviews = len(reviews)
    ratings = [r.rating for r in reviews]
    product.avg_rating = sum(ratings) / len(ratings)
    db.commit()
    
    # Trigger Analysis
    background_tasks.add_task(run_complete_analysis, product.id)
    
    return {
        "message": "OnePlus demo created",
        "product_id": product.id,
        "frontend_url": f"http://localhost:3000/products/{product.id}"
    }

async def background_scrape_flipkart(product_id: int, url: str):
    """Background task to scrape Flipkart reviews."""
    print(f"Starting background scrape for {product_id}...")
    scraper = FlipkartScraper()
    reviews = await scraper.scrape_reviews(url, max_reviews=50) # Get up to 50
    print(f"Scraped {len(reviews)} reviews for {product_id}")
    
    db = SessionLocal()
    try:
        for r in reviews:
            review = Review(
                product_id=product_id,
                review_text=r['text'],
                rating=r['rating'],
                reviewer_name=r['reviewer_name'],
                verified_purchase=r['verified'],
                review_date=r['date']
            )
            db.add(review)
        db.commit()
        print(f"Saved {len(reviews)} reviews to DB")
        
        # Run Analysis
        await run_complete_analysis(product_id)
        
    except Exception as e:
        print(f"Error in background task: {e}")
    finally:
        db.close()

@router.post("/demo/oneplus-flipkart")
async def create_oneplus_flipkart_demo(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Create a demo product using REAL data scraped from Flipkart.
    """
    scraper = FlipkartScraper()
    url = await scraper.find_product_url_from_search("https://www.flipkart.com/search?q=OnePlus+13R")
    
    if not url:
        return {"error": "Could not find OnePlus 13R on Flipkart"}
    
    print(f"Found Flipkart URL: {url}")

    # Check for existing
    existing = db.query(Product).filter(Product.name.ilike("%OnePlus 13R%Flipkart%")).first()
    if existing:
        # Re-trigger analysis just in case
        background_tasks.add_task(run_complete_analysis, existing.id)
        return {
            "message": "Demo product already exists, re-analyzing.",
            "product_id": existing.id,
            "frontend_url": f"http://localhost:3000/products/{existing.id}"
        }
        
    # Create Product
    product = Product(
        name="OnePlus 13R (Flipkart Real Data)",
        url=url + "?demo_id=" + str(uuid.uuid4()), # Unique URL
        platform="Flipkart"
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Scrape reviews in background
    background_tasks.add_task(background_scrape_flipkart, product.id, url)
    
    return {
        "message": "Created product! Scraping and analyzing reviews in background (wait 1-2 mins).",
        "product_id": product.id,
        "frontend_url": f"http://localhost:3000/products/{product.id}"
    }
