from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import can_access_athlete, get_current_user
from app.db.database import get_db
from app.db.models import TrainingProgram, TrainingSession, User, UserRole
from app.schemas.schemas import SessionCompleteRequest, TrainingProgramGenerateRequest
from app.services.activity_service import log_activity
from app.services.analytics_service import (
    adapt_training_program,
    evaluate_user_achievements,
    generate_training_program,
)

router = APIRouter(prefix="/api/training", tags=["Personalized Training Programs"])


def _serialize_program(p: TrainingProgram, athlete_name: Optional[str] = None) -> dict:
    sessions_sorted = sorted(p.sessions, key=lambda s: s.day_index)
    completed_count = sum(1 for s in sessions_sorted if s.is_completed)
    return {
        "id": p.id,
        "athlete_id": p.athlete_id,
        "athlete_name": athlete_name,
        "title": p.title,
        "sport": p.sport,
        "goal": p.goal,
        "experience_level": p.experience_level,
        "weekly_target_sessions": p.weekly_target_sessions,
        "weekly_target_calories": p.weekly_target_calories,
        "status": p.status,
        "adaptation_notes": p.adaptation_notes,
        "generated_by_ai": p.generated_by_ai,
        "completion_pct": round((completed_count / max(len(sessions_sorted), 1)) * 100.0, 1),
        "created_at": p.created_at.isoformat(),
        "sessions": [
            {
                "id": s.id,
                "day_of_week": s.day_of_week,
                "day_index": s.day_index,
                "exercise_type": s.exercise_type,
                "focus_area": s.focus_area,
                "target_duration_minutes": s.target_duration_minutes,
                "target_heart_rate_bpm": s.target_heart_rate_bpm,
                "expected_calories": s.expected_calories,
                "intensity": s.intensity,
                "instructions": s.instructions,
                "is_completed": s.is_completed,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "feedback_rpe": s.feedback_rpe,
                "feedback_notes": s.feedback_notes,
            }
            for s in sessions_sorted
        ],
    }


@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_program(
    payload: TrainingProgramGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_id = payload.athlete_id or current_user.id
    if not can_access_athlete(current_user, target_id, db):
        raise HTTPException(status_code=403, detail="Access denied for this athlete.")
    athlete = db.query(User).filter(User.id == target_id).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found.")

    program = generate_training_program(
        db=db,
        athlete=athlete,
        created_by=current_user,
        title=payload.title,
        sport=payload.sport,
        goal=payload.goal,
        experience_level=payload.experience_level,
        weekly_sessions=payload.weekly_sessions,
    )
    log_activity(
        db,
        current_user.id,
        "training_program_generated",
        "training_program",
        f"Generated personalized plan '{program.title}' for {athlete.full_name}.",
        entity_id=program.id,
    )
    return _serialize_program(program, athlete.full_name)


@router.get("/programs")
def list_programs(
    athlete_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role_val = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role)
    q = db.query(TrainingProgram)
    if athlete_id:
        if not can_access_athlete(current_user, athlete_id, db):
            raise HTTPException(status_code=403, detail="Access denied.")
        q = q.filter(TrainingProgram.athlete_id == athlete_id)
    elif role_val == UserRole.ATHLETE.value:
        q = q.filter(TrainingProgram.athlete_id == current_user.id)

    programs = q.order_by(TrainingProgram.created_at.desc()).limit(25).all()
    users = {u.id: u.full_name for u in db.query(User).all()}
    return [_serialize_program(p, users.get(p.athlete_id)) for p in programs]


@router.patch("/sessions/{session_id}/complete")
def complete_training_session(
    session_id: int,
    payload: SessionCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sess = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Training session not found.")
    program = sess.program
    if not can_access_athlete(current_user, program.athlete_id, db):
        raise HTTPException(status_code=403, detail="Access denied.")

    sess.is_completed = payload.is_completed
    sess.completed_at = datetime.now(timezone.utc) if payload.is_completed else None
    if payload.feedback_rpe is not None:
        sess.feedback_rpe = payload.feedback_rpe
    if payload.feedback_notes is not None:
        sess.feedback_notes = payload.feedback_notes

    db.commit()
    db.refresh(program)
    unlocked = evaluate_user_achievements(db, program.athlete_id)
    athlete = db.query(User).filter(User.id == program.athlete_id).first()
    out = _serialize_program(program, athlete.full_name if athlete else None)
    out["newly_unlocked_badges"] = unlocked
    return out


@router.post("/programs/{program_id}/adapt")
def adapt_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    program = db.query(TrainingProgram).filter(TrainingProgram.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Training program not found.")
    if not can_access_athlete(current_user, program.athlete_id, db):
        raise HTTPException(status_code=403, detail="Access denied.")

    updated = adapt_training_program(db, program)
    log_activity(
        db,
        current_user.id,
        "training_program_adapted",
        "training_program",
        f"Adapted training program '{updated.title}' based on completed session feedback.",
        entity_id=updated.id,
    )
    athlete = db.query(User).filter(User.id == updated.athlete_id).first()
    return _serialize_program(updated, athlete.full_name if athlete else None)
