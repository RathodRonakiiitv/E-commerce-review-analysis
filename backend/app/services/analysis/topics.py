"""Topic modeling service using Gensim LDA."""
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List

from gensim import corpora
from gensim.models import LdaModel
from sqlalchemy.orm import Session

from app.models import Review, Topic

logger = logging.getLogger(__name__)

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
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)
    words = text.split()
    words = [w for w in words if w not in STOPWORDS and len(w) > 2]
    return words


def run_lda(documents: List[List[str]], num_topics: int = 5, num_words: int = 10) -> List[Dict]:
    """
    Run Latent Dirichlet Allocation using Gensim.

    Args:
        documents: List of tokenized documents (list of word lists).
        num_topics: Number of topics to discover.
        num_words: Number of keywords per topic.

    Returns:
        List of dicts with 'keywords' and 'doc_count' for each topic.
    """
    if len(documents) < 5:
        logger.info("Too few documents (%d) for meaningful LDA — skipping", len(documents))
        return []

    # Build dictionary and corpus
    dictionary = corpora.Dictionary(documents)

    # Adaptive filtering: relax thresholds for small corpora
    no_below = max(2, len(documents) // 20)
    no_above = 0.7 if len(documents) < 30 else 0.6
    dictionary.filter_extremes(no_below=no_below, no_above=no_above)

    if len(dictionary) < 5:
        logger.warning("Dictionary too small (%d terms) after filtering — skipping LDA", len(dictionary))
        return []

    corpus = [dictionary.doc2bow(doc) for doc in documents]
    # Remove empty documents from corpus
    corpus = [bow for bow in corpus if bow]

    if len(corpus) < 5:
        logger.warning("Too few non-empty documents (%d) — skipping LDA", len(corpus))
        return []

    # Don't request more topics than we have documents
    effective_topics = min(num_topics, max(2, len(corpus) // 3))

    # Train LDA model
    lda_model = LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=effective_topics,
        random_state=42,
        passes=10,
        alpha="auto",
        eta="auto",
        per_word_topics=True,
    )

    # Assign each document to its dominant topic
    topic_doc_counts = [0] * effective_topics
    for bow in corpus:
        topic_dist = lda_model.get_document_topics(bow)
        if topic_dist:
            dominant = max(topic_dist, key=lambda x: x[1])[0]
            topic_doc_counts[dominant] += 1

    # Build results
    results = []
    for topic_id in range(effective_topics):
        # Get top words for this topic
        keywords = [word for word, _ in lda_model.show_topic(topic_id, topn=num_words)]

        if topic_doc_counts[topic_id] < 2:
            continue  # skip topics with too few documents

        results.append({
            "keywords": keywords,
            "doc_count": topic_doc_counts[topic_id],
        })

    logger.info("LDA training complete: %d topics discovered", len(results))
    return results


def generate_topic_label(keywords: List[str]) -> str:
    """Generate a human-readable label for a topic."""
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

    return keywords[0].capitalize() + " Related"


async def analyze_product_topics(db: Session, product_id: int, num_topics: int = 5) -> Dict:
    """
    Perform topic modeling on product reviews using Gensim LDA.

    Returns:
        Dictionary with discovered topics.
    """
    reviews = db.query(Review).filter(Review.product_id == product_id).all()

    if not reviews:
        return {
            "product_id": product_id,
            "topics": [],
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    # Preprocess all reviews
    documents = [preprocess_text(r.review_text) for r in reviews]
    documents = [d for d in documents if len(d) >= 3]

    if len(documents) < 10:
        return {
            "product_id": product_id,
            "topics": [],
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    # Clear existing topics
    db.query(Topic).filter(Topic.product_id == product_id).delete()

    # Run LDA
    topic_results = run_lda(documents, num_topics=num_topics)

    # Build response and save to DB
    topics = []
    for i, topic in enumerate(topic_results):
        keywords = topic["keywords"][:10]
        label = generate_topic_label(keywords)

        topic_record = Topic(
            product_id=product_id,
            topic_number=i + 1,
            topic_keywords=keywords,
            topic_label=label,
            review_count=topic["doc_count"],
        )
        db.add(topic_record)

        # Get sample reviews for this topic
        sample_reviews = []
        primary_keyword = keywords[0]
        for review in reviews[:50]:
            if primary_keyword in review.review_text.lower():
                sample_reviews.append(review.review_text[:150] + "...")
                if len(sample_reviews) >= 3:
                    break

        topics.append({
            "topic_number": i + 1,
            "topic_label": label,
            "keywords": keywords,
            "review_count": topic["doc_count"],
            "sample_reviews": sample_reviews,
        })

    db.commit()
    logger.info("Topic analysis complete for product %d: %d topics", product_id, len(topics))

    return {
        "product_id": product_id,
        "topics": topics,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }
