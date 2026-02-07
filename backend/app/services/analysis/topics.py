"""Topic modeling service using LDA."""
import re
from datetime import datetime
from typing import Dict, List
from collections import Counter

from sqlalchemy.orm import Session

from app.models import Review, Topic

# Common English stopwords
STOPWORDS = set([
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she",
    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that",
    "these", "those", "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of",
    "at", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just",
    "don", "should", "now", "product", "amazon", "flipkart", "buy", "bought",
    "one", "get", "got", "use", "used", "using", "also", "really", "would",
    "could", "like", "much", "even", "still", "well", "back", "time"
])


def preprocess_text(text: str) -> List[str]:
    """Clean and tokenize text."""
    # Lowercase and remove special characters
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)
    
    # Tokenize
    words = text.split()
    
    # Remove stopwords and short words
    words = [w for w in words if w not in STOPWORDS and len(w) > 2]
    
    return words


def simple_lda(documents: List[List[str]], num_topics: int = 5, num_words: int = 10) -> List[Dict]:
    """
    Simple topic modeling using word frequency analysis.
    For production, use gensim LDA.
    """
    # Count word frequencies overall
    word_freq = Counter()
    doc_word_freq = []
    
    for doc in documents:
        doc_counter = Counter(doc)
        doc_word_freq.append(doc_counter)
        word_freq.update(doc)
    
    # Get top words
    top_words = [word for word, _ in word_freq.most_common(100)]
    
    # Cluster documents based on which top words they contain most
    # This is a simplified approach - real LDA would be better
    
    # Group by most frequent word in each doc
    word_to_docs = {word: [] for word in top_words[:num_topics * 3]}
    
    for i, doc_counter in enumerate(doc_word_freq):
        for word in top_words[:num_topics * 3]:
            if word in doc_counter:
                word_to_docs[word].append(i)
    
    # Select top topic words based on document coverage
    topic_words = []
    used_words = set()
    
    for word in top_words:
        if word not in used_words and len(topic_words) < num_topics:
            # Find related words (co-occurring)
            related = []
            docs_with_word = word_to_docs.get(word, [])
            
            if len(docs_with_word) >= 3:  # Minimum documents
                co_occur = Counter()
                for doc_idx in docs_with_word:
                    for w in documents[doc_idx]:
                        if w != word and w not in used_words:
                            co_occur[w] += 1
                
                related = [w for w, _ in co_occur.most_common(num_words - 1)]
                used_words.add(word)
                used_words.update(related[:5])
                
                topic_words.append({
                    "keywords": [word] + related,
                    "doc_count": len(docs_with_word)
                })
    
    return topic_words


def generate_topic_label(keywords: List[str]) -> str:
    """Generate a human-readable label for a topic."""
    # Map common keywords to labels
    label_map = {
        "battery": "Battery Performance",
        "charge": "Charging Experience",
        "screen": "Display Quality",
        "display": "Display Quality",
        "camera": "Camera Quality",
        "photo": "Photography",
        "delivery": "Shipping & Delivery",
        "shipping": "Shipping & Delivery",
        "price": "Value for Money",
        "money": "Value for Money",
        "quality": "Build Quality",
        "build": "Build Quality",
        "sound": "Audio Quality",
        "speaker": "Speaker Performance",
        "performance": "Device Performance",
        "speed": "Performance & Speed",
        "design": "Design & Aesthetics",
        "color": "Appearance",
        "service": "Customer Service",
        "support": "Customer Support",
    }
    
    for keyword in keywords[:3]:
        if keyword in label_map:
            return label_map[keyword]
    
    # Default: capitalize first keyword
    return keywords[0].capitalize() + " Related"


async def analyze_product_topics(db: Session, product_id: int, num_topics: int = 5) -> Dict:
    """
    Perform topic modeling on product reviews.
    
    Returns:
        Dictionary with discovered topics
    """
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    
    if not reviews:
        return {
            "product_id": product_id,
            "topics": [],
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    # Preprocess all reviews
    documents = [preprocess_text(r.review_text) for r in reviews]
    documents = [d for d in documents if len(d) >= 3]  # Filter short docs
    
    if len(documents) < 10:
        return {
            "product_id": product_id,
            "topics": [],
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    # Clear existing topics
    db.query(Topic).filter(Topic.product_id == product_id).delete()
    
    # Run topic modeling
    topic_results = simple_lda(documents, num_topics=num_topics)
    
    # Build response and save to DB
    topics = []
    for i, topic in enumerate(topic_results):
        keywords = topic["keywords"][:10]
        label = generate_topic_label(keywords)
        
        # Save to database
        topic_record = Topic(
            product_id=product_id,
            topic_number=i + 1,
            topic_keywords=keywords,
            topic_label=label,
            review_count=topic["doc_count"]
        )
        db.add(topic_record)
        
        # Get sample reviews for this topic
        sample_reviews = []
        primary_keyword = keywords[0]
        for review in reviews[:50]:  # Check first 50
            if primary_keyword in review.review_text.lower():
                sample_reviews.append(review.review_text[:150] + "...")
                if len(sample_reviews) >= 3:
                    break
        
        topics.append({
            "topic_number": i + 1,
            "topic_label": label,
            "keywords": keywords,
            "review_count": topic["doc_count"],
            "sample_reviews": sample_reviews
        })
    
    db.commit()
    
    return {
        "product_id": product_id,
        "topics": topics,
        "analyzed_at": datetime.utcnow().isoformat()
    }
