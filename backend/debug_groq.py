from app.config import get_settings
from app.services.ai.groq_service import groq_service

settings = get_settings()
print(f"Groq API Key loaded: {'Yes' if settings.groq_api_key else 'No'}")
print(f"Groq Model loaded: {settings.groq_model}")

if settings.groq_api_key:
    # censored key for safety
    print(f"Key start: {settings.groq_api_key[:4]}...")

import asyncio
try:
    # Test a simple call
    print("Testing connection...")
    res = asyncio.run(groq_service.generate_review_summary([{'text': 'test', 'rating': 5}], 'Test Product'))
    print(f"Result: {res}")
except Exception as e:
    print(f"Error: {e}")
