"""
Fake Review Classifier — Training Pipeline

Uses TF-IDF text features + handcrafted features with Logistic Regression.
Produces a serialized model + evaluation metrics (precision, recall, F1,
confusion matrix) saved to backend/app/ml/model/.

Run:  python -m app.ml.train_fake_classifier
"""
import json
import os
import pickle
import re
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from scipy.sparse import hstack, csr_matrix

from app.ml.dataset import LABELED_REVIEWS

# ─── Paths ───────────────────────────────────────────────────────────
MODEL_DIR = Path(__file__).resolve().parent / "model"
MODEL_PATH = MODEL_DIR / "fake_classifier.pkl"
VECTORIZER_PATH = MODEL_DIR / "tfidf_vectorizer.pkl"
METRICS_PATH = MODEL_DIR / "metrics.json"

# ─── Generic phrases list (shared with fake_detection heuristics) ────
GENERIC_PHRASES = [
    "good product", "nice product", "best product", "worst product",
    "highly recommend", "do not buy", "waste of money", "value for money",
    "must buy", "don't buy", "excellent", "terrible", "amazing", "horrible",
    "five stars", "one star", "5 stars", "1 star",
]


# ─── Feature Engineering ─────────────────────────────────────────────

def extract_handcrafted_features(review: Dict) -> List[float]:
    """
    Extract 8 numerical features from a review dict.

    Features:
        0. word_count           — number of words
        1. avg_word_length      — average word length
        2. exclamation_ratio    — exclamations per word
        3. caps_ratio           — fraction of uppercase chars
        4. rating_extremity     — 1 if rating is 1 or 5, else 0
        5. generic_phrase_count — count of generic pattern matches
        6. unique_word_ratio    — unique words / total words (lexical diversity)
        7. is_verified          — 1 if verified purchase, else 0
    """
    text = review["text"]
    rating = review.get("rating", 3)
    verified = review.get("verified", True)

    words = text.split()
    word_count = max(len(words), 1)
    avg_word_len = np.mean([len(w) for w in words]) if words else 0

    exclamation_count = text.count("!")
    exclamation_ratio = exclamation_count / word_count

    upper_chars = sum(1 for c in text if c.isupper())
    caps_ratio = upper_chars / max(len(text), 1)

    rating_extremity = 1.0 if rating in (1, 5) else 0.0

    text_lower = text.lower()
    generic_count = sum(1 for p in GENERIC_PHRASES if p in text_lower)

    unique_words = set(w.lower().strip(".,!?;:") for w in words)
    unique_ratio = len(unique_words) / word_count

    is_verified = 1.0 if verified else 0.0

    return [
        word_count,
        avg_word_len,
        exclamation_ratio,
        caps_ratio,
        rating_extremity,
        generic_count,
        unique_ratio,
        is_verified,
    ]


# ─── Training ────────────────────────────────────────────────────────

def prepare_data() -> Tuple[List[str], np.ndarray, np.ndarray]:
    """
    Convert LABELED_REVIEWS into (texts, handcrafted_features, labels).
    """
    texts = [r["text"] for r in LABELED_REVIEWS]
    features = np.array([extract_handcrafted_features(r) for r in LABELED_REVIEWS])
    labels = np.array([r["label"] for r in LABELED_REVIEWS])
    return texts, features, labels


def train_and_evaluate() -> Dict:
    """
    Train TF-IDF + Logistic Regression on the labeled dataset.

    Uses 5-fold stratified cross-validation to produce honest metrics,
    then retrains on the full dataset for the production model.

    Returns:
        Dictionary with evaluation metrics.
    """
    texts, handcrafted, labels = prepare_data()

    # ── TF-IDF vectorizer ──────────────────────────────────────────
    tfidf = TfidfVectorizer(
        max_features=3000,
        ngram_range=(1, 2),       # unigrams + bigrams
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
        strip_accents="unicode",
    )

    # ── 5-fold Stratified Cross-Validation ─────────────────────────
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_predictions = np.zeros(len(labels))

    print("Running 5-fold stratified cross-validation...")
    for fold, (train_idx, val_idx) in enumerate(skf.split(texts, labels), 1):
        # Split
        train_texts = [texts[i] for i in train_idx]
        val_texts = [texts[i] for i in val_idx]
        train_hc = handcrafted[train_idx]
        val_hc = handcrafted[val_idx]
        train_y = labels[train_idx]

        # TF-IDF fit on train fold
        tfidf_train = tfidf.fit_transform(train_texts)
        tfidf_val = tfidf.transform(val_texts)

        # Scale handcrafted features
        scaler = StandardScaler()
        hc_train = scaler.fit_transform(train_hc)
        hc_val = scaler.transform(val_hc)

        # Combine
        X_train = hstack([tfidf_train, csr_matrix(hc_train)])
        X_val = hstack([tfidf_val, csr_matrix(hc_val)])

        # Train
        clf = LogisticRegression(
            C=1.0, max_iter=1000, class_weight="balanced", random_state=42
        )
        clf.fit(X_train, train_y)

        # Predict
        cv_predictions[val_idx] = clf.predict(X_val)

        fold_acc = accuracy_score(labels[val_idx], cv_predictions[val_idx])
        print(f"  Fold {fold}: accuracy = {fold_acc:.3f}")

    # ── Cross-validation metrics ───────────────────────────────────
    cv_preds = cv_predictions.astype(int)
    cv_accuracy = accuracy_score(labels, cv_preds)
    cv_precision = precision_score(labels, cv_preds, zero_division=0)
    cv_recall = recall_score(labels, cv_preds, zero_division=0)
    cv_f1 = f1_score(labels, cv_preds, zero_division=0)
    cv_cm = confusion_matrix(labels, cv_preds).tolist()
    cv_report = classification_report(
        labels, cv_preds, target_names=["Genuine", "Fake"], output_dict=True
    )

    print(f"\n{'='*50}")
    print("Cross-Validation Results (5-fold)")
    print(f"{'='*50}")
    print(f"  Accuracy:  {cv_accuracy:.3f}")
    print(f"  Precision: {cv_precision:.3f}")
    print(f"  Recall:    {cv_recall:.3f}")
    print(f"  F1 Score:  {cv_f1:.3f}")
    print(f"  Confusion Matrix:")
    print(f"    TN={cv_cm[0][0]}  FP={cv_cm[0][1]}")
    print(f"    FN={cv_cm[1][0]}  TP={cv_cm[1][1]}")
    print()
    print(classification_report(labels, cv_preds, target_names=["Genuine", "Fake"]))

    # ── Retrain on full dataset for production ─────────────────────
    print("Training final model on full dataset...")
    tfidf_final = TfidfVectorizer(
        max_features=3000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
        strip_accents="unicode",
    )
    X_tfidf = tfidf_final.fit_transform(texts)

    scaler_final = StandardScaler()
    hc_scaled = scaler_final.fit_transform(handcrafted)
    X_full = hstack([X_tfidf, csr_matrix(hc_scaled)])

    clf_final = LogisticRegression(
        C=1.0, max_iter=1000, class_weight="balanced", random_state=42
    )
    clf_final.fit(X_full, labels)

    # Full-dataset accuracy (training accuracy — for reference only)
    train_preds = clf_final.predict(X_full)
    train_accuracy = accuracy_score(labels, train_preds)
    print(f"  Training accuracy: {train_accuracy:.3f}")

    # ── Save artifacts ─────────────────────────────────────────────
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"classifier": clf_final, "scaler": scaler_final}, f)
    print(f"  Model saved:      {MODEL_PATH}")

    with open(VECTORIZER_PATH, "wb") as f:
        pickle.dump(tfidf_final, f)
    print(f"  Vectorizer saved: {VECTORIZER_PATH}")

    # ── Save metrics ───────────────────────────────────────────────
    metrics = {
        "dataset_size": len(labels),
        "genuine_count": int((labels == 0).sum()),
        "fake_count": int((labels == 1).sum()),
        "cross_validation": {
            "folds": 5,
            "accuracy": round(cv_accuracy, 4),
            "precision": round(cv_precision, 4),
            "recall": round(cv_recall, 4),
            "f1_score": round(cv_f1, 4),
            "confusion_matrix": {
                "true_negatives": cv_cm[0][0],
                "false_positives": cv_cm[0][1],
                "false_negatives": cv_cm[1][0],
                "true_positives": cv_cm[1][1],
            },
            "classification_report": cv_report,
        },
        "training_accuracy": round(train_accuracy, 4),
        "features": {
            "tfidf": {
                "max_features": 3000,
                "ngram_range": [1, 2],
                "description": "TF-IDF weighted unigrams and bigrams from review text",
            },
            "handcrafted": [
                "word_count",
                "avg_word_length",
                "exclamation_ratio",
                "caps_ratio",
                "rating_extremity",
                "generic_phrase_count",
                "unique_word_ratio",
                "is_verified",
            ],
        },
        "model": "LogisticRegression(C=1.0, class_weight='balanced')",
    }

    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"  Metrics saved:    {METRICS_PATH}")

    return metrics


if __name__ == "__main__":
    train_and_evaluate()
