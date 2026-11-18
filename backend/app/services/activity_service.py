from typing import Optional
from sqlalchemy.orm import Session
from app.db.models import ActivityLog


def log_activity(
    db: Session,
    user_id: Optional[int],
    action: str,
    entity_type: str,
    summary: str,
    entity_id: Optional[int] = None,
) -> ActivityLog:
    entry = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary[:300],
    )
    db.add(entry)
    db.commit()
    return entry
