"""CLI script to train the Companion Strain/Readiness Classifier and Semantic Coaching NLP AI."""

import json

from app.db.database import SessionLocal
from app.db.init_db import init_db
from app.ml.coaching_ai_engine import coaching_ai_engine


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        metrics = coaching_ai_engine.train_all(db)
        print("=== TRAINED COMPANION COACHING AI METRICS ===")
        print(json.dumps(metrics, indent=2))

        print("\n=== SEMANTIC NLP RETRIEVAL VERIFICATION ===")
        test_queries = [
            "How do I improve my 5K running speed and VO2max?",
            "What is ACWR workload injury risk?",
            "How much protein and sleep do athletes need for recovery?",
            "How should I peak and taper before competition?",
        ]
        for q in test_queries:
            res = coaching_ai_engine.retrieve_coaching_knowledge(q, top_k=1)
            top = res["matches"][0] if res["matches"] else None
            print(f"Q: {q}")
            print(f"  Intent={res['predicted_intent']} | Sim={top['similarity_score'] if top else 0} | Match={top['question'] if top else None}")

        print("\n=== STRAIN & READINESS ZONE VERIFICATION ===")
        print(coaching_ai_engine.predict_strain_zone(28, 55, 165, 5, 6.2, 2.0, 75, 560))
    finally:
        db.close()


if __name__ == "__main__":
    main()
