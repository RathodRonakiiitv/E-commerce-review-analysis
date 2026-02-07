"""Product model for storing e-commerce product information."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    """Represents a product from an e-commerce platform."""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=True)
    url = Column(Text, unique=True, nullable=False, index=True)
    platform = Column(String(50), default="amazon")  # amazon, flipkart
    total_reviews = Column(Integer, default=0)
    avg_rating = Column(Numeric(2, 1), nullable=True)
    scraped_at = Column(DateTime, nullable=True)
    last_analyzed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    analysis_cache = relationship("AnalysisCache", back_populates="product", cascade="all, delete-orphan")
    topics = relationship("Topic", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name[:30] if self.name else 'N/A'}...')>"
