import sys
import os
import random
import uuid
from datetime import datetime, timedelta

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, init_db
from app.models import Product, Review
from app.services.analysis.runner import run_complete_analysis
import asyncio

# Product Details
PRODUCT_NAME = "OnePlus 13R (Charcoal, 8GB RAM, 128GB Storage)"
PRODUCT_URL = "https://www.amazon.in/OnePlus-Charcoal-Snapdragon-Personalised-Game-Changing/dp/B0FZSXYV6K"

# Realistic Reviews for OnePlus 13R
POSITIVE_REVIEWS = [
    "The Snapdragon 8 Gen 2 processor is a beast! Gaming is buttery smooth, getting constant 120fps on BGMI. Battery life is also amazing.",
    "Classic OnePlus experience. OxygenOS is clean and fast. The 120Hz display looks stunning specifically for media consumption.",
    "Best phone under 40k due to the performance. Camera is decent, but the main highlight is the raw speed and charging. 0 to 100 in 30 mins!",
    "Switching from iPhone to OnePlus and I'm impressed. The haptics are great and the alert slider is so convenient.",
    "Build quality is premium. The charcoal color looks very sophisticated. No heating issues so far even after heavy gaming sessions.",
    "Battery backup is phenomenal. Easily lasts 1.5 days with moderate usage. The 100W charging is a game changer.",
    "Display quality is top notch. HDR content looks great on Netflix. Typical OnePlus flagship killer vibes.",
    "Highly recommended for gamers! The touch sampling rate is high and there's no lag. Heat management is better than 11R.",
    "Value for money product. You get flagship specs at a mid-range price. Call quality and network reception are also solid.",
    "Love the fast charging. I forgot to charge at night, plugged it in while showering and it was 85% done!"
]

NEGATIVE_REVIEWS = [
    "Camera is average at best. Low light photos have too much noise. Expected better from Sony IMX sensor.",
    "Front camera washes out skin tones. It applies automatically beauty mode which I hate.",
    "Curved display causes accidentally touches. Flat screen would have been better for gaming.",
    "Bloatware in OxygenOS! Found some pre-installed junk apps. OnePlus is losing its clean software identity.",
    "No wireless charging support. At this price point, it should have been included.",
    "Heating up slightly while charging with the 100W brick. Got scared and turned it off.",
    "Ultrawide camera is useless, only 8MP details are soft. Only main camera is good."
]

NEUTRAL_REVIEWS = [
    "It's a good phone but not a huge upgrade from 11R. Buy it only if you have an older device.",
    "Decent performance but battery drains faster on 5G. Needs software optimization.",
    "Good phone but the design is getting boring. Same circular camera module for 3 years now.",
    "Okay for daily use. Camera could be better. Fast charging is the only saving grace.",
    "Missing the IP68 rating. Only getting fake promises on water resistance."
]

async def seed_oneplus():
    print(f"Creating simulation for: {PRODUCT_NAME}")
    
    db = SessionLocal()
    
    try:
        # Check if product exists and delete it
        existing_product = db.query(Product).filter(Product.url == PRODUCT_URL).first()
        if existing_product:
            print(f"Found existing product {existing_product.id}, deleting...")
            db.delete(existing_product)
            db.commit()
            print("Deleted existing product.")

        # Create Product
        product = Product(
            url=PRODUCT_URL,
            platform="amazon",
            name=PRODUCT_NAME,
            total_reviews=0,
            avg_rating=0.0,
            scraped_at=datetime.utcnow()
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        product_id = product.id
        print(f"Product created with ID: {product_id}")
        
        # Generate Reviews
        reviews_data = []
        
        # Add 35 Positive
        for i in range(35):
            reviews_data.append({
                "text": random.choice(POSITIVE_REVIEWS),
                "rating": random.choice([4, 5, 5]),
                "name": f"OnePlus User {i}"
            })
            
        # Add 10 Negative
        for i in range(10):
            reviews_data.append({
                "text": random.choice(NEGATIVE_REVIEWS),
                "rating": random.choice([1, 2, 2]),
                "name": f"Disappointed Customer {i}"
            })
            
        # Add 5 Neutral
        for i in range(5):
            reviews_data.append({
                "text": random.choice(NEUTRAL_REVIEWS),
                "rating": 3,
                "name": f"Verified Buyer {i}"
            })
            
        random.shuffle(reviews_data)
        
        # Insert Reviews
        for review_data in reviews_data:
            review = Review(
                product_id=product_id,
                review_text=review_data["text"],
                rating=review_data["rating"],
                review_date=(datetime.now() - timedelta(days=random.randint(1, 60))).date(),
                reviewer_name=review_data["name"],
                verified_purchase=True,
                helpful_count=random.randint(0, 20)
            )
            db.add(review)
            
        db.commit()
        print(f"Inserted {len(reviews_data)} reviews")
        
        print("\nSUCCESS! Product created.")
        print(f"To run analysis, visit: http://localhost:8000/api/products/{product_id}/reanalyze (POST)")
        print(f"View result at: http://localhost:3000/products/{product_id}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Just run the sync part for now to debug
    # But wait, main part is async def seed_oneplus
    # Let's adapt
    asyncio.run(seed_oneplus())
