"""Analysis-related models for aspects, topics, and cached results."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class ReviewAspect(Base):
    """Stores aspect-based sentiment for individual reviews."""
    
    __tablename__ = "review_aspects"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    
    aspect_name = Column(String(50), nullable=False)  # quality, price, delivery, etc.
    sentiment = Column(String(20), nullable=True)  # positive, negative, neutral
    sentiment_score = Column(Numeric(4, 3), nullable=True)
    mentioned_text = Column(Text, nullable=True)  # The sentence mentioning this aspect
    
    # Relationship
    review = relationship("Review", back_populates="aspects")
    
    def __repr__(self):
        return f"<ReviewAspect(aspect='{self.aspect_name}', sentiment='{self.sentiment}')>"


class AnalysisCache(Base):
    """Cached analysis results for products."""
    
    __tablename__ = "analysis_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    analysis_type = Column(String(50), nullable=False)  # overall, aspects, topics, insights
    results = Column(JSON, nullable=False)  # Store analysis as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationship
    product = relationship("Product", back_populates="analysis_cache")
    
    def __repr__(self):
        return f"<AnalysisCache(type='{self.analysis_type}', product_id={self.product_id})>"


class Topic(Base):
    """Discovered topics from LDA modeling."""
    
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    topic_number = Column(Integer, nullable=False)
    topic_keywords = Column(JSON, nullable=True)  # List of keywords stored as JSON
    topic_label = Column(String(100), nullable=True)  # Human-readable label
    review_count = Column(Integer, default=0)  # How many reviews belong to this topic
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    product = relationship("Product", back_populates="topics")
    
    def __repr__(self):
        return f"<Topic(number={self.topic_number}, label='{self.topic_label}')>"
