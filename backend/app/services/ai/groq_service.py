"""Groq AI service for intelligent review analysis and suggestions."""
import logging
from typing import List, Dict, Optional
import httpx


from app.config import get_settings

logger = logging.getLogger(__name__)

class GroqService:
    """Service for Groq API integration."""
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.groq_api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = settings.groq_model
        if self.api_key:
            logger.info(f"Groq API configured with key: {self.api_key[:8]}... model: {self.model}")
        else:
            logger.warning("Groq API key not found! AI features will be disabled.")
    
    async def generate_review_summary(self, reviews: List[Dict], product_name: str) -> Dict:
        """
        Generate an AI summary of product reviews.
        
        Args:
            reviews: List of review dictionaries with text and rating
            product_name: Name of the product
            
        Returns:
            AI-generated summary and insights
        """
        if not self.api_key:
            return {
                "error": "Groq API key not configured",
                "summary": None,
                "suggestions": []
            }
        
        # Prepare review text (limit to avoid token limits)
        review_sample = reviews[:20]  # Take top 20 reviews
        review_texts = "\n".join([
            f"- Rating: {r.get('rating', 'N/A')}/5 | {r.get('sentiment', 'unknown')}: {r.get('text', '')[:300]}"
            for r in review_sample
        ])
        
        prompt = f"""Analyze these customer reviews for "{product_name}" and provide:

1. **Executive Summary** (2-3 sentences): Overall product perception
2. **Key Strengths** (bullet points): What customers love most
3. **Key Weaknesses** (bullet points): Common complaints
4. **Purchase Recommendation**: Should someone buy this? Why/why not?
5. **Suggested Improvements**: What should the manufacturer improve?

Reviews:
{review_texts}

Provide a helpful, balanced analysis."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert product analyst. Provide concise, actionable insights from customer reviews. Be balanced and helpful."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data["choices"][0]["message"]["content"]
                    
                    return {
                        "summary": ai_response,
                        "model": self.model,
                        "reviews_analyzed": len(review_sample),
                        "error": None
                    }
                else:
                    error_detail = response.text
                    logger.error(f"Groq API error {response.status_code}: {error_detail}")
                    return {
                        "error": f"Groq API error: {response.status_code} - {error_detail[:200]}",
                        "summary": None,
                        "details": error_detail
                    }
                    
        except Exception as e:
            return {
                "error": str(e),
                "summary": None
            }
    
    async def generate_aspect_deep_dive(self, aspect: str, reviews: List[Dict], product_name: str) -> Dict:
        """
        Generate AI analysis for a specific aspect (e.g., battery, quality).
        """
        if not self.api_key:
            return {"error": "Groq API key not configured"}
        
        # Filter reviews mentioning the aspect
        aspect_reviews = [r for r in reviews if aspect.lower() in r.get('text', '').lower()][:15]
        
        if not aspect_reviews:
            return {"summary": f"No reviews specifically mention {aspect}.", "error": None}
        
        review_texts = "\n".join([
            f"- {r.get('text', '')[:250]}"
            for r in aspect_reviews
        ])
        
        prompt = f"""Analyze what customers say about "{aspect}" for "{product_name}":

Reviews mentioning {aspect}:
{review_texts}

Provide:
1. Overall sentiment about {aspect}
2. Specific praise (if any)
3. Specific complaints (if any)
4. Comparison to expectations

Keep it concise (3-4 sentences max)."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a product analyst. Be concise and helpful."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "aspect": aspect,
                        "summary": data["choices"][0]["message"]["content"],
                        "reviews_analyzed": len(aspect_reviews),
                        "error": None
                    }
                else:
                    return {"error": f"Groq API error: {response.status_code}"}
                    
        except Exception as e:
            return {"error": str(e)}
    
    async def suggest_response_to_review(self, review_text: str, sentiment: str) -> Dict:
        """
        Generate a suggested response for a seller to reply to a review.
        """
        if not self.api_key:
            return {"error": "Groq API key not configured"}
        
        prompt = f"""A customer left this {sentiment} review:
"{review_text}"

Write a professional, empathetic seller response (2-3 sentences) that:
- Thanks the customer
- Addresses their specific points
- Offers help if negative, appreciation if positive"""

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a professional customer service representative."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.8,
                        "max_tokens": 200
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "suggested_response": data["choices"][0]["message"]["content"],
                        "error": None
                    }
                else:
                    return {"error": f"Groq API error: {response.status_code}"}
                    
        except Exception as e:
            return {"error": str(e)}


# Singleton instance
groq_service = GroqService()
