from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import can_access_athlete, get_current_user, require_roles
from app.db.database import get_db
from app.db.models import InjuryRiskAssessment, User, UserRole
from app.schemas.schemas import InjuryRiskRunRequest
from app.services.activity_service import log_activity
from app.services.analytics_service import assess_injury_risk

router = APIRouter(prefix="/api/injury", tags=["Injury Risk & Prevention"])


def _serialize_risk(a: InjuryRiskAssessment, athlete_name: Optional[str] = None) -> dict:
    return {
        "id": a.id,
        "athlete_id": a.athlete_id,
        "athlete_name": athlete_name,
        "risk_score": a.risk_score,
        "risk_level": a.risk_level,
        "acute_load_7d": a.acute_load_7d,
        "chronic_load_28d": a.chronic_load_28d,
        "acwr": a.acwr,
        "anomalies_detected": a.anomalies_detected or [],
        "risk_factors": a.risk_factors or [],
        "preventive_exercises": a.preventive_exercises or [],
        "training_modifications": a.training_modifications or [],
        "coach_alert_required": a.coach_alert_required,
        "coach_acknowledged": a.coach_acknowledged,
        "disclaimer": a.disclaimer,
        "created_at": a.created_at.isoformat(),
    }


@router.post("/assess", status_code=status.HTTP_201_CREATED)
def run_injury_risk_assessment(
    payload: InjuryRiskRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_id = payload.athlete_id or current_user.id
    if not can_access_athlete(current_user, target_id, db):
        raise HTTPException(status_code=403, detail="Access denied for this athlete.")
    athlete = db.query(User).filter(User.id == target_id).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found.")

    assessment = assess_injury_risk(db, athlete, current_user)
    log_activity(
        db,
        current_user.id,
        "injury_risk_assessed",
        "injury_risk",
        f"Workload risk assessment for {athlete.full_name}: {assessment.risk_level} ({assessment.risk_score}/100).",
        entity_id=assessment.id,
    )
    return _serialize_risk(assessment, athlete.full_name)


@router.get("/assessments")
def list_injury_assessments(
    athlete_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role_val = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role)
    q = db.query(InjuryRiskAssessment)
    if athlete_id:
        if not can_access_athlete(current_user, athlete_id, db):
            raise HTTPException(status_code=403, detail="Access denied.")
        q = q.filter(InjuryRiskAssessment.athlete_id == athlete_id)
    elif role_val == UserRole.ATHLETE.value:
        q = q.filter(InjuryRiskAssessment.athlete_id == current_user.id)

    rows = q.order_by(InjuryRiskAssessment.created_at.desc()).limit(50).all()
    users = {u.id: u.full_name for u in db.query(User).all()}
    return [_serialize_risk(r, users.get(r.athlete_id)) for r in rows]


@router.patch("/assessments/{assessment_id}/acknowledge")
def acknowledge_coach_alert(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.COACH, UserRole.ANALYST)),
):
    assessment = db.query(InjuryRiskAssessment).filter(InjuryRiskAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    assessment.coach_acknowledged = True
    db.commit()
    db.refresh(assessment)
    athlete = db.query(User).filter(User.id == assessment.athlete_id).first()
    log_activity(
        db,
        current_user.id,
        "injury_alert_acknowledged",
        "injury_risk",
        f"{current_user.full_name} acknowledged workload alert for {athlete.full_name if athlete else 'athlete'}.",
        entity_id=assessment.id,
    )
    return _serialize_risk(assessment, athlete.full_name if athlete else None)
