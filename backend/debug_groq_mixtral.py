from app.config import get_settings
from app.services.ai.groq_service import groq_service
import asyncio
import os
import json

# Force reload settings to be safe
os.environ["GROQ_MODEL"] = "mixtral-8x7b-32768" 

settings = get_settings()
print(f"Key start: {settings.groq_api_key[:10]}...")

try:
    print("Testing with model: mixtral-8x7b-32768")
    groq_service.model = "mixtral-8x7b-32768"
    # We need to simulate the request manually to get full error if service swallows it
    # But service prints error.
    res = asyncio.run(groq_service.generate_review_summary([{'text': 'Great phone!', 'rating': 5}], 'Test Product'))
    print(f"Result: {res}")
except Exception as e:
    print(f"Error: {e}")
