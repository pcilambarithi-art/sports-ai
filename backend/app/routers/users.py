from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import can_access_athlete, get_current_user, require_roles
from app.db.database import get_db
from app.db.models import (
    AIPrediction,
    AthleteProfile,
    CoachAthleteLink,
    CoachProfile,
    InjuryRiskAssessment,
    PerformanceRecord,
    SkillAssessment,
    TrainingProgram,
    User,
    UserRole,
)
from app.routers.auth import serialize_user
from app.schemas.schemas import AdminUserUpdate, AssignAthleteRequest, UserProfileUpdate
from app.services.activity_service import log_activity

router = APIRouter(prefix="/api/users", tags=["Users & Profiles"])


@router.get("")
def list_users(
    role: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_role = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role)
    q = db.query(User)
    if role:
        try:
            q = q.filter(User.role == UserRole(role))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role filter.")

    # Athletes see themselves plus coaches/staff directory; admins/coaches/analysts see all matching users
    if current_role == UserRole.ATHLETE.value and role not in {"coach"}:
        q = q.filter((User.id == current_user.id) | (User.role == UserRole.COACH))

    users = q.order_by(User.created_at.desc()).all()
    return [serialize_user(u) for u in users]


@router.put("/me")
def update_my_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _apply_profile_update(db, current_user, payload, current_user)


@router.put("/{user_id}/profile")
def update_user_profile(
    user_id: int,
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")

    role_val = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role)
    if current_user.id != user_id and role_val not in {UserRole.ADMIN.value, UserRole.COACH.value}:
        raise HTTPException(status_code=403, detail="Not permitted to edit this profile.")

    return _apply_profile_update(db, target, payload, current_user)


def _apply_profile_update(db: Session, target: User, payload: UserProfileUpdate, actor: User) -> dict:
    if payload.full_name is not None:
        target.full_name = payload.full_name.strip()
        target.avatar_initials = "".join(p[0].upper() for p in target.full_name.split()[:2])[:4]
    if payload.bio is not None:
        target.bio = payload.bio.strip()

    if payload.athlete_profile is not None:
        ap = target.athlete_profile
        if not ap:
            ap = AthleteProfile(user_id=target.id)
            db.add(ap)
        for field, val in payload.athlete_profile.model_dump(exclude_unset=True).items():
            setattr(ap, field, val)

    if payload.coach_profile is not None:
        cp = target.coach_profile
        if not cp:
            cp = CoachProfile(user_id=target.id)
            db.add(cp)
        for field, val in payload.coach_profile.model_dump(exclude_unset=True).items():
            setattr(cp, field, val)

    db.commit()
    db.refresh(target)
    log_activity(
        db,
        actor.id,
        "profile_updated",
        "user",
        f"Updated profile for {target.full_name}.",
        entity_id=target.id,
    )
    return serialize_user(target)


@router.patch("/{user_id}/admin")
def admin_update_user(
    user_id: int,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    if payload.role is not None:
        target.role = UserRole(payload.role)
        if target.role == UserRole.ATHLETE and not target.athlete_profile:
            db.add(AthleteProfile(user_id=target.id))
        if target.role == UserRole.COACH and not target.coach_profile:
            db.add(CoachProfile(user_id=target.id))
    if payload.is_active is not None:
        if target.id == current_user.id and not payload.is_active:
            raise HTTPException(status_code=400, detail="Admin cannot deactivate their own account.")
        target.is_active = payload.is_active

    db.commit()
    db.refresh(target)
    log_activity(
        db,
        current_user.id,
        "admin_user_updated",
        "user",
        f"Admin updated user {target.email} (role={target.role.value}, active={target.is_active}).",
        entity_id=target.id,
    )
    return serialize_user(target)


@router.post("/assignments", status_code=status.HTTP_201_CREATED)
def assign_athlete_to_coach(
    payload: AssignAthleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.COACH)),
):
    coach = db.query(User).filter(User.id == payload.coach_id, User.role == UserRole.COACH).first()
    athlete = db.query(User).filter(User.id == payload.athlete_id, User.role == UserRole.ATHLETE).first()
    if not coach or not athlete:
        raise HTTPException(status_code=404, detail="Valid coach and athlete IDs are required.")

    existing = (
        db.query(CoachAthleteLink)
        .filter(
            CoachAthleteLink.coach_id == payload.coach_id,
            CoachAthleteLink.athlete_id == payload.athlete_id,
        )
        .first()
    )
    if existing:
        existing.notes = payload.notes
        db.commit()
        return {"id": existing.id, "coach_id": coach.id, "athlete_id": athlete.id, "notes": existing.notes}

    link = CoachAthleteLink(
        coach_id=coach.id, athlete_id=athlete.id, notes=payload.notes
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    log_activity(
        db,
        current_user.id,
        "coach_assigned",
        "assignment",
        f"Assigned athlete {athlete.full_name} to coach {coach.full_name}.",
        entity_id=link.id,
    )
    return {"id": link.id, "coach_id": coach.id, "athlete_id": athlete.id, "notes": link.notes}


@router.get("/assignments")
def list_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    links = db.query(CoachAthleteLink).order_by(CoachAthleteLink.assigned_at.desc()).all()
    users = {u.id: u for u in db.query(User).all()}
    return [
        {
            "id": l.id,
            "coach_id": l.coach_id,
            "coach_name": users[l.coach_id].full_name if l.coach_id in users else "Unknown",
            "athlete_id": l.athlete_id,
            "athlete_name": users[l.athlete_id].full_name if l.athlete_id in users else "Unknown",
            "notes": l.notes,
            "assigned_at": l.assigned_at.isoformat(),
        }
        for l in links
    ]


@router.get("/{athlete_id}/overview")
def get_athlete_overview(
    athlete_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not can_access_athlete(current_user, athlete_id, db):
        raise HTTPException(status_code=403, detail="Access denied for this athlete.")
    athlete = db.query(User).filter(User.id == athlete_id).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found.")

    records = (
        db.query(PerformanceRecord)
        .filter(PerformanceRecord.athlete_id == athlete_id)
        .order_by(PerformanceRecord.session_date.desc())
        .limit(20)
        .all()
    )
    predictions = (
        db.query(AIPrediction)
        .filter(AIPrediction.athlete_id == athlete_id)
        .order_by(AIPrediction.created_at.desc())
        .limit(10)
        .all()
    )
    latest_risk = (
        db.query(InjuryRiskAssessment)
        .filter(InjuryRiskAssessment.athlete_id == athlete_id)
        .order_by(InjuryRiskAssessment.created_at.desc())
        .first()
    )
    latest_skill = (
        db.query(SkillAssessment)
        .filter(SkillAssessment.athlete_id == athlete_id)
        .order_by(SkillAssessment.created_at.desc())
        .first()
    )
    active_program = (
        db.query(TrainingProgram)
        .filter(TrainingProgram.athlete_id == athlete_id, TrainingProgram.status == "active")
        .order_by(TrainingProgram.created_at.desc())
        .first()
    )

    return {
        "user": serialize_user(athlete),
        "counts": {
            "sessions": len(records),
            "predictions": len(predictions),
            "has_active_program": active_program is not None,
        },
        "recent_sessions": [
            {
                "id": r.id,
                "session_date": r.session_date.isoformat(),
                "exercise_type": r.exercise_type,
                "duration_minutes": r.duration_minutes,
                "heart_rate_bpm": r.heart_rate_bpm,
                "calories_burned": r.calories_burned,
                "ai_predicted_calories": r.ai_predicted_calories,
                "rpe_score": r.rpe_score,
            }
            for r in records
        ],
        "recent_predictions": [
            {
                "id": p.id,
                "exercise_type": p.exercise_type,
                "duration_minutes": p.duration_minutes,
                "heart_rate_bpm": p.heart_rate_bpm,
                "predicted_calories": p.predicted_calories,
                "burn_rate_per_min": p.burn_rate_per_min,
                "created_at": p.created_at.isoformat(),
            }
            for p in predictions
        ],
        "latest_injury_risk": (
            {
                "risk_score": latest_risk.risk_score,
                "risk_level": latest_risk.risk_level,
                "acwr": latest_risk.acwr,
                "coach_alert_required": latest_risk.coach_alert_required,
                "created_at": latest_risk.created_at.isoformat(),
            }
            if latest_risk
            else None
        ),
        "latest_skill": (
            {
                "overall_score": latest_skill.overall_score,
                "dataset_peer_percentile": latest_skill.dataset_peer_percentile,
                "created_at": latest_skill.created_at.isoformat(),
            }
            if latest_skill
            else None
        ),
    }
