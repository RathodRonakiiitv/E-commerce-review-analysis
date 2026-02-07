"""Review model for storing individual product reviews."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Numeric, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.database import Base


class Review(Base):
    """Represents a single review for a product."""
    
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Review content
    review_text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    review_date = Column(Date, nullable=True)
    reviewer_name = Column(String(200), nullable=True)
    
    # Metadata
    verified_purchase = Column(Boolean, default=False)
    helpful_count = Column(Integer, default=0)
    
    # Analysis results
    sentiment_label = Column(String(20), nullable=True)  # positive, negative, neutral
    sentiment_score = Column(Numeric(4, 3), nullable=True)  # 0.000 to 1.000
    is_suspicious = Column(Boolean, default=False)
    suspicious_score = Column(Integer, default=0)  # 0-100
    
    # Timestamps
    scraped_at = Column(DateTime, default=datetime.utcnow)
    analyzed_at = Column(DateTime, nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="reviews")
    aspects = relationship("ReviewAspect", back_populates="review", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Review(id={self.id}, rating={self.rating}, sentiment='{self.sentiment_label}')>"
