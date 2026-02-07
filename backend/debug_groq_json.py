from app.config import get_settings
from app.services.ai.groq_service import groq_service
import asyncio
import os
import json

# Force reload settings to be safe
os.environ["GROQ_MODEL"] = "llama3-70b-8192" 

settings = get_settings()
print(f"Key start: {settings.groq_api_key[:10]}...")

try:
    print("Testing with model: llama3-70b-8192")
    groq_service.model = "llama3-70b-8192"
    res = asyncio.run(groq_service.generate_review_summary([{'text': 'Great phone!', 'rating': 5}], 'Test Product'))
    print(f"Result: {res}")
except Exception as e:
    # Try to print the inner error dictionary if available
    if hasattr(e, 'response') and e.response:
         print(f"Align Error Response: {e.response.json()}")
    else:
         print(f"Error: {e}")
