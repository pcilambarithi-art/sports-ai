import io
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.security import can_access_athlete, get_current_user
from app.db.database import get_db
from app.db.models import AthleteProfile, PerformanceRecord, User, UserRole
from app.ml.model_service import model_service
from app.schemas.schemas import PerformanceRecordCreate
from app.services.activity_service import log_activity
from app.services.analytics_service import (
    _safe_athlete_defaults,
    compute_predictive_analytics,
    evaluate_user_achievements,
)

router = APIRouter(prefix="/api/performance", tags=["Performance Analysis"])


def _serialize_record(r: PerformanceRecord, athlete_name: Optional[str] = None) -> dict:
    return {
        "id": r.id,
        "athlete_id": r.athlete_id,
        "athlete_name": athlete_name,
        "session_date": r.session_date.isoformat(),
        "sport": r.sport,
        "exercise_type": r.exercise_type,
        "duration_minutes": r.duration_minutes,
        "heart_rate_bpm": r.heart_rate_bpm,
        "speed_kmh": r.speed_kmh,
        "distance_km": r.distance_km,
        "calories_burned": r.calories_burned,
        "ai_predicted_calories": r.ai_predicted_calories,
        "rpe_score": r.rpe_score,
        "fatigue_level": r.fatigue_level,
        "sleep_hours": r.sleep_hours,
        "water_intake_liters": r.water_intake_liters,
        "notes": r.notes,
        "created_at": r.created_at.isoformat(),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_performance_record(
    payload: PerformanceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_id = payload.athlete_id or current_user.id
    if not can_access_athlete(current_user, target_id, db):
        raise HTTPException(status_code=403, detail="Access denied for this athlete.")
    athlete = db.query(User).filter(User.id == target_id).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found.")

    ai_pred_val: Optional[float] = None
    if payload.auto_predict_calories and model_service.status == "ready":
        try:
            profile = db.query(AthleteProfile).filter(AthleteProfile.user_id == target_id).first()
            defaults = _safe_athlete_defaults(profile)
            raw = dict(defaults)
            raw["Exercise_Type"] = payload.exercise_type
            raw["Duration_Minutes"] = payload.duration_minutes
            raw["Heart_Rate_BPM"] = payload.heart_rate_bpm
            if payload.sleep_hours is not None:
                raw["Sleep_Hours"] = payload.sleep_hours
            if payload.water_intake_liters is not None:
                raw["Water_Intake_Liters"] = payload.water_intake_liters
            ai_pred_val = model_service.predict_batch_fast([raw])[0]
        except Exception:
            ai_pred_val = None

    rec = PerformanceRecord(
        athlete_id=target_id,
        logged_by_id=current_user.id,
        session_date=payload.session_date or datetime.now(timezone.utc),
        sport=payload.sport or (athlete.athlete_profile.sport if athlete.athlete_profile else None),
        exercise_type=payload.exercise_type,
        duration_minutes=payload.duration_minutes,
        heart_rate_bpm=payload.heart_rate_bpm,
        speed_kmh=payload.speed_kmh,
        distance_km=payload.distance_km,
        calories_burned=payload.calories_burned,
        ai_predicted_calories=ai_pred_val,
        rpe_score=payload.rpe_score,
        fatigue_level=payload.fatigue_level,
        sleep_hours=payload.sleep_hours,
        water_intake_liters=payload.water_intake_liters,
        notes=payload.notes,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    log_activity(
        db,
        current_user.id,
        "performance_logged",
        "performance",
        f"Logged {rec.exercise_type} ({rec.duration_minutes:.0f} min @ {rec.heart_rate_bpm:.0f} BPM) for {athlete.full_name}.",
        entity_id=rec.id,
    )
    unlocked = evaluate_user_achievements(db, target_id)
    out = _serialize_record(rec, athlete.full_name)
    out["newly_unlocked_badges"] = unlocked
    return out


@router.get("")
def list_performance_records(
    athlete_id: Optional[int] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role_val = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role)
    q = db.query(PerformanceRecord)
    if athlete_id:
        if not can_access_athlete(current_user, athlete_id, db):
            raise HTTPException(status_code=403, detail="Access denied.")
        q = q.filter(PerformanceRecord.athlete_id == athlete_id)
    elif role_val == UserRole.ATHLETE.value:
        q = q.filter(PerformanceRecord.athlete_id == current_user.id)

    rows = q.order_by(PerformanceRecord.session_date.desc()).limit(limit).all()
    users = {u.id: u.full_name for u in db.query(User).all()}
    return [_serialize_record(r, users.get(r.athlete_id)) for r in rows]


@router.get("/forecast")
def get_predictive_forecast(
    athlete_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_id = athlete_id or current_user.id
    if not can_access_athlete(current_user, target_id, db):
        raise HTTPException(status_code=403, detail="Access denied.")
    return compute_predictive_analytics(db, target_id)


@router.get("/export")
def export_performance_csv(
    athlete_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = list_performance_records(athlete_id=athlete_id, limit=500, db=db, current_user=current_user)
    df = pd.DataFrame(data)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=performance_records_export.csv"},
    )
