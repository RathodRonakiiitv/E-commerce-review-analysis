from app.config import get_settings
from app.services.ai.groq_service import groq_service
import asyncio
import os

# Force reload settings to be safe (though new process handles it)
os.environ["GROQ_MODEL"] = "llama3-8b-8192" 

settings = get_settings()
print(f"Key start: {settings.groq_api_key[:10]}...")

try:
    print("Testing with model: llama3-8b-8192")
    # Manually override model for test
    groq_service.model = "llama3-8b-8192"
    res = asyncio.run(groq_service.generate_review_summary([{'text': 'Great phone!', 'rating': 5}], 'Test Product'))
    print(f"Result: {res}")
except Exception as e:
    print(f"Error: {e}")
