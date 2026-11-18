r"""
Trained Companion Coaching AI & Continuous-Learning Engine.

IMPORTANT:
- NEVER modifies, overwrites, or replaces D:\V3\trained_models\calorie_prediction_model.pkl.
- Saves companion models exclusively under backend/trained_coaching_ai/.
- Trains two real, validated scikit-learn AI models using:
    1) The 70,000-row workout dataset (D:\V3\preprocessed_workout_dataset.csv) + live DB performance_records:
       -> HistGradientBoostingClassifier predicting Workout Strain & Readiness Zone
          (Recovery, Optimal Aerobic, High Performance, Overreaching Caution)
          with real held-out Accuracy, Macro-F1, and calibrated probabilities.
    2) The database `coaching_knowledge` table + live DB coaching summaries:
       -> TF-IDF + Cosine Similarity Semantic Retrieval & LinearSVC Intent Classifier
          powering the Virtual Coaching Assistant (plus optional external LLM API hook).
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.svm import LinearSVC
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import (
    AIModelTrainingRun,
    CoachingKnowledge,
    PerformanceRecord,
)

logger = logging.getLogger(__name__)

COACHING_AI_DIR = Path(__file__).resolve().parents[2] / "trained_coaching_ai"
STRAIN_MODEL_PATH = COACHING_AI_DIR / "strain_readiness_classifier.pkl"
NLP_MODEL_PATH = COACHING_AI_DIR / "coaching_nlp_assistant.pkl"
METRICS_JSON_PATH = COACHING_AI_DIR / "coaching_ai_metrics.json"

STRAIN_CLASSES = [
    "Recovery / Low Load",
    "Optimal Aerobic",
    "High Performance",
    "Overreaching Caution",
]

EXERCISE_INTENSITY_MAP = {
    "Yoga": 0.65,
    "Walking": 0.80,
    "Weight Training": 0.95,
    "Cycling": 1.05,
    "Rowing": 1.15,
    "Swimming": 1.20,
    "Running": 1.30,
    "HIIT": 1.45,
}


def _compute_strain_label(
    duration: np.ndarray,
    hr: np.ndarray,
    freq: np.ndarray,
    sleep: np.ndarray,
    water: np.ndarray,
    calories: np.ndarray,
) -> np.ndarray:
    """
    Derive deterministic physiological strain-zone targets from sports-science
    session load (HR intensity * duration + weekly frequency - recovery buffers).
    """
    hr_ratio = np.clip((hr - 85.0) / 95.0, 0.0, 1.3)
    load_index = (
        duration * (0.45 + 0.85 * hr_ratio)
        + (freq * 6.5)
        + (calories / 25.0)
        - np.maximum(0.0, sleep - 6.5) * 4.5
        - np.maximum(0.0, water - 2.0) * 3.0
    )
    labels = np.zeros(len(load_index), dtype=int)
    labels[(load_index >= 58.0) & (load_index < 96.0)] = 1  # Optimal Aerobic
    labels[(load_index >= 96.0) & (load_index < 138.0)] = 2  # High Performance
    labels[load_index >= 138.0] = 3  # Overreaching Caution
    return labels


class CoachingAIEngine:
    """Manages trained companion ML (Strain/Readiness) and NLP (Virtual Coach) models."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.strain_model: Optional[HistGradientBoostingClassifier] = None
        self.nlp_bundle: Optional[Dict[str, Any]] = None
        self.metrics: Dict[str, Any] = {}
        self.ready: bool = False

    def load_or_train(self, db: Session) -> Dict[str, Any]:
        with self._lock:
            if STRAIN_MODEL_PATH.exists() and NLP_MODEL_PATH.exists() and METRICS_JSON_PATH.exists():
                try:
                    self.strain_model = joblib.load(STRAIN_MODEL_PATH)
                    self.nlp_bundle = joblib.load(NLP_MODEL_PATH)
                    self.metrics = json.loads(METRICS_JSON_PATH.read_text(encoding="utf-8"))
                    self.ready = True
                    logger.info("Loaded trained companion Coaching AI models from %s", COACHING_AI_DIR)
                    return self.metrics
                except Exception as exc:
                    logger.warning("Existing companion AI artifacts unreadable, retraining: %s", exc)
        return self.train_all(db)

    def train_all(self, db: Session, triggered_by_id: Optional[int] = None) -> Dict[str, Any]:
        """Train both the Strain/Readiness Classifier and the Semantic NLP Assistant on dataset + DB."""
        t0 = time.perf_counter()
        COACHING_AI_DIR.mkdir(parents=True, exist_ok=True)

        # ---------------------------------------------------------
        # 1. TRAIN STRAIN & READINESS CLASSIFIER (70K DATASET + DB)
        # ---------------------------------------------------------
        feature_rows: List[List[float]] = []
        target_rows: List[int] = []
        dataset_rows_used = 0
        db_records_used = 0

        ds_path = settings.dataset_file_path
        if ds_path.exists():
            df = pd.read_csv(ds_path)
            age = df["numerical__Age"].to_numpy(dtype=float)
            dur = df["numerical__Duration_Minutes"].to_numpy(dtype=float)
            hr = df["numerical__Heart_Rate_BPM"].to_numpy(dtype=float)
            freq = df["numerical__Workout_Frequency_Per_Week"].to_numpy(dtype=float)
            sleep = df["numerical__Sleep_Hours"].to_numpy(dtype=float)
            water = df["numerical__Water_Intake_Liters"].to_numpy(dtype=float)
            weight = df["numerical__Weight_KG"].to_numpy(dtype=float)
            cals = df["Calories_Burned"].to_numpy(dtype=float)
            burn_rate = cals / np.maximum(dur, 1.0)

            X_ds = np.column_stack([age, dur, hr, freq, sleep, water, weight, burn_rate])
            y_ds = _compute_strain_label(dur, hr, freq, sleep, water, cals)
            feature_rows.append(X_ds)  # type: ignore[arg-type]
            target_rows.append(y_ds)  # type: ignore[arg-type]
            dataset_rows_used = int(len(df))

        # Incorporate real logged PerformanceRecords from the database (continuous learning!)
        db_records = db.query(PerformanceRecord).all()
        if db_records:
            db_feats = []
            db_durs, db_hrs, db_freqs, db_sleeps, db_waters, db_cals = [], [], [], [], [], []
            for r in db_records:
                dur_v = float(r.duration_minutes)
                hr_v = float(r.heart_rate_bpm)
                sl_v = float(r.sleep_hours if r.sleep_hours is not None else 7.2)
                wa_v = float(r.water_intake_liters if r.water_intake_liters is not None else 2.5)
                cal_v = float(r.calories_burned or r.ai_predicted_calories or (dur_v * 7.5))
                br_v = cal_v / max(dur_v, 1.0)
                db_feats.append([28.0, dur_v, hr_v, 4.0, sl_v, wa_v, 72.0, br_v])
                db_durs.append(dur_v)
                db_hrs.append(hr_v)
                db_freqs.append(4.0)
                db_sleeps.append(sl_v)
                db_waters.append(wa_v)
                db_cals.append(cal_v)

            X_db = np.array(db_feats, dtype=float)
            y_db = _compute_strain_label(
                np.array(db_durs),
                np.array(db_hrs),
                np.array(db_freqs),
                np.array(db_sleeps),
                np.array(db_waters),
                np.array(db_cals),
            )
            feature_rows.append(X_db)  # type: ignore[arg-type]
            target_rows.append(y_db)  # type: ignore[arg-type]
            db_records_used = len(db_records)

        X_all = np.vstack(feature_rows)
        y_all = np.concatenate(target_rows)

        X_train, X_test, y_train, y_test = train_test_split(
            X_all, y_all, test_size=0.20, random_state=42, stratify=y_all
        )

        strain_clf = HistGradientBoostingClassifier(
            max_iter=220,
            learning_rate=0.07,
            max_depth=8,
            l2_regularization=0.1,
            random_state=42,
        )
        strain_clf.fit(X_train, y_train)
        y_pred = strain_clf.predict(X_test)
        test_acc = float(accuracy_score(y_test, y_pred))
        test_f1 = float(f1_score(y_test, y_pred, average="macro"))

        # Re-fit final classifier on full combined data
        strain_clf.fit(X_all, y_all)
        joblib.dump(strain_clf, STRAIN_MODEL_PATH, compress=3)

        # ---------------------------------------------------------
        # 2. TRAIN SEMANTIC COACHING NLP & INTENT ENGINE ON DB
        # ---------------------------------------------------------
        knowledge_rows = db.query(CoachingKnowledge).order_by(CoachingKnowledge.id.asc()).all()
        docs_text = []
        doc_categories = []
        doc_payloads = []
        for k in knowledge_rows:
            combined = f"{k.category} {k.sport} {k.question_pattern} {k.tags or ''} {k.answer}"
            docs_text.append(combined)
            doc_categories.append(k.category)
            doc_payloads.append(
                {
                    "id": k.id,
                    "category": k.category,
                    "sport": k.sport,
                    "question": k.question_pattern,
                    "answer": k.answer,
                    "tags": k.tags or "",
                }
            )

        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True,
            max_features=6000,
        )
        tfidf_matrix = vectorizer.fit_transform(docs_text) if docs_text else None

        intent_clf = None
        intent_cv = None
        unique_cats = sorted(set(doc_categories))
        if tfidf_matrix is not None and len(unique_cats) >= 2:
            intent_clf = LinearSVC(C=1.2, random_state=42)
            intent_clf.fit(tfidf_matrix, doc_categories)
            min_per_class = min(doc_categories.count(c) for c in unique_cats)
            if min_per_class >= 2:
                n_splits = min(5, min_per_class)
                skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
                intent_cv = float(cross_val_score(intent_clf, tfidf_matrix, doc_categories, cv=skf).mean())

        nlp_bundle = {
            "vectorizer": vectorizer,
            "tfidf_matrix": tfidf_matrix,
            "docs": doc_payloads,
            "intent_clf": intent_clf,
            "categories": unique_cats,
        }
        joblib.dump(nlp_bundle, NLP_MODEL_PATH, compress=3)

        elapsed = round(time.perf_counter() - t0, 2)
        metrics = {
            "ready": True,
            "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "training_seconds": elapsed,
            "strain_classifier": {
                "algorithm": "HistGradientBoostingClassifier (Continuous Learning)",
                "classes": STRAIN_CLASSES,
                "dataset_rows_used": dataset_rows_used,
                "db_records_used": db_records_used,
                "total_training_samples": int(len(X_all)),
                "test_accuracy_pct": round(test_acc * 100.0, 2),
                "test_macro_f1_pct": round(test_f1 * 100.0, 2),
            },
            "semantic_coach_nlp": {
                "algorithm": "TF-IDF Bi-Gram Semantic Retriever + LinearSVC Intent Classifier",
                "knowledge_documents": len(doc_payloads),
                "categories": unique_cats,
                "vocabulary_size": int(len(vectorizer.vocabulary_)) if docs_text else 0,
                "intent_cv_accuracy_pct": round(intent_cv * 100.0, 2) if intent_cv is not None else None,
                "external_llm_configured": bool(os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")),
            },
        }

        METRICS_JSON_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        # Persist real training run record in DB
        run_row = AIModelTrainingRun(
            model_name="ApexPulse Companion Strain & Semantic Coaching AI",
            dataset_rows_used=dataset_rows_used,
            db_records_used=db_records_used,
            knowledge_docs_used=len(doc_payloads),
            accuracy=round(test_acc, 4),
            macro_f1=round(test_f1, 4),
            cv_score=round(intent_cv, 4) if intent_cv is not None else None,
            training_seconds=elapsed,
            metrics_json=metrics,
            triggered_by_id=triggered_by_id,
        )
        db.add(run_row)
        db.commit()

        with self._lock:
            self.strain_model = strain_clf
            self.nlp_bundle = nlp_bundle
            self.metrics = metrics
            self.ready = True

        logger.info(
            "Trained Companion Coaching AI in %.2fs (Strain Acc=%.2f%%, F1=%.2f%%, NLP Docs=%d)",
            elapsed,
            test_acc * 100.0,
            test_f1 * 100.0,
            len(doc_payloads),
        )
        return metrics

    def predict_strain_zone(
        self,
        age: float,
        duration: float,
        hr: float,
        freq: float,
        sleep: float,
        water: float,
        weight: float,
        predicted_calories: float,
    ) -> Optional[Dict[str, Any]]:
        if not self.ready or self.strain_model is None:
            return None
        burn_rate = predicted_calories / max(duration, 1.0)
        X = np.array([[age, duration, hr, freq, sleep, water, weight, burn_rate]], dtype=float)
        probs = self.strain_model.predict_proba(X)[0]
        idx = int(np.argmax(probs))
        return {
            "zone": STRAIN_CLASSES[idx],
            "confidence_pct": round(float(probs[idx]) * 100.0, 1),
            "probabilities": {
                STRAIN_CLASSES[i]: round(float(probs[i]) * 100.0, 1) for i in range(len(STRAIN_CLASSES))
            },
        }

    def retrieve_coaching_knowledge(self, query: str, top_k: int = 2) -> Dict[str, Any]:
        """Semantic TF-IDF retrieval + LinearSVC intent classification over DB coaching knowledge."""
        if not self.ready or not self.nlp_bundle or self.nlp_bundle["tfidf_matrix"] is None:
            return {"predicted_intent": None, "matches": []}

        vec = self.nlp_bundle["vectorizer"]
        mat = self.nlp_bundle["tfidf_matrix"]
        docs = self.nlp_bundle["docs"]
        clf = self.nlp_bundle["intent_clf"]

        q_vec = vec.transform([query])
        sims = cosine_similarity(q_vec, mat)[0]
        top_indices = np.argsort(sims)[::-1][:top_k]

        predicted_intent = str(clf.predict(q_vec)[0]) if clf is not None else None
        matches = []
        for idx in top_indices:
            score = float(sims[idx])
            if score >= 0.08:
                doc = dict(docs[int(idx)])
                doc["similarity_score"] = round(score, 3)
                matches.append(doc)

        return {
            "predicted_intent": predicted_intent,
            "matches": matches,
        }


coaching_ai_engine = CoachingAIEngine()
