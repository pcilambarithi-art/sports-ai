"""Database table initialization and static achievement catalog seeding (no fake user stats)."""

from sqlalchemy.orm import Session

from app.db.database import Base, engine
from app.db.models import Achievement

DEFAULT_ACHIEVEMENTS = [
    {
        "code": "FIRST_PREDICTION",
        "name": "Data-Driven Debut",
        "description": "Completed your first live AI calorie burn prediction using the trained model.",
        "icon": "sparkles",
        "points": 50,
        "category": "ai",
    },
    {
        "code": "FIVE_PREDICTIONS",
        "name": "Analytics Regular",
        "description": "Logged 5 or more AI workout predictions.",
        "icon": "bar-chart",
        "points": 120,
        "category": "ai",
    },
    {
        "code": "FIRST_SESSION",
        "name": "Session Starter",
        "description": "Logged your first real training performance record.",
        "icon": "flame",
        "points": 50,
        "category": "training",
    },
    {
        "code": "CONSISTENCY_3",
        "name": "Momentum Builder",
        "description": "Logged 3 or more training sessions.",
        "icon": "calendar-check",
        "points": 150,
        "category": "consistency",
    },
    {
        "code": "ENDURANCE_1000",
        "name": "Kilocalorie Crusher",
        "description": "Accumulated 1,000+ total calories across logged training sessions.",
        "icon": "zap",
        "points": 200,
        "category": "milestone",
    },
    {
        "code": "VIDEO_BREAKDOWN",
        "name": "Film Room Analyst",
        "description": "Uploaded and analyzed a training video using OpenCV movement tracking.",
        "icon": "video",
        "points": 100,
        "category": "video",
    },
    {
        "code": "PLAN_COMPLETED",
        "name": "Plan Executor",
        "description": "Completed at least 3 scheduled sessions in a personalized training program.",
        "icon": "award",
        "points": 175,
        "category": "training",
    },
    {
        "code": "CHALLENGE_FINISHER",
        "name": "Challenge Conqueror",
        "description": "Completed a training motivation challenge.",
        "icon": "trophy",
        "points": 250,
        "category": "challenge",
    },
]


def init_db(db: Session | None = None) -> None:
    """Create all tables if they don't exist and seed badge definitions."""
    Base.metadata.create_all(bind=engine)
    own_session = db is None
    if own_session:
        from app.db.database import SessionLocal

        db = SessionLocal()
    try:
        for item in DEFAULT_ACHIEVEMENTS:
            existing = db.query(Achievement).filter(Achievement.code == item["code"]).first()
            if not existing:
                db.add(Achievement(**item))
        db.commit()
    finally:
        if own_session:
            db.close()
