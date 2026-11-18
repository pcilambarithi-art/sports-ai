from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import can_access_athlete, get_current_user, require_roles
from app.db.database import get_db
from app.db.models import (
    Achievement,
    Challenge,
    ChallengeParticipation,
    SkillAssessment,
    User,
    UserAchievement,
    UserRole,
)
from app.schemas.schemas import (
    ChallengeCreate,
    ChallengeProgressUpdate,
    SkillAssessmentRunRequest,
)
from app.services.activity_service import log_activity
from app.services.analytics_service import (
    build_leaderboard,
    evaluate_skill_assessment,
    evaluate_user_achievements,
)

router = APIRouter(tags=["Skill Assessment & Gamification"])


def _serialize_skill(s: SkillAssessment, athlete_name: Optional[str] = None) -> dict:
    return {
        "id": s.id,
        "athlete_id": s.athlete_id,
        "athlete_name": athlete_name,
        "overall_score": s.overall_score,
        "consistency_score": s.consistency_score,
        "aerobic_efficiency_score": s.aerobic_efficiency_score,
        "energy_output_score": s.energy_output_score,
        "recovery_discipline_score": s.recovery_discipline_score,
        "workload_capacity_score": s.workload_capacity_score,
        "dataset_peer_percentile": s.dataset_peer_percentile,
        "db_cohort_rank": s.db_cohort_rank,
        "db_cohort_total": s.db_cohort_total,
        "criteria_breakdown": s.criteria_breakdown or {},
        "strengths": s.strengths or [],
        "improvement_areas": s.improvement_areas or [],
        "sessions_analyzed": s.sessions_analyzed,
        "predictions_analyzed": s.predictions_analyzed,
        "created_at": s.created_at.isoformat(),
    }


@router.post("/api/skills/assess", status_code=status.HTTP_201_CREATED)
def run_skill_assessment(
    payload: SkillAssessmentRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_id = payload.athlete_id or current_user.id
    if not can_access_athlete(current_user, target_id, db):
        raise HTTPException(status_code=403, detail="Access denied for this athlete.")
    athlete = db.query(User).filter(User.id == target_id).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found.")

    try:
        assessment = evaluate_skill_assessment(db, athlete, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_activity(
        db,
        current_user.id,
        "skill_assessed",
        "skill_assessment",
        f"Evaluated skill score for {athlete.full_name}: {assessment.overall_score}/100.",
        entity_id=assessment.id,
    )
    return _serialize_skill(assessment, athlete.full_name)


@router.get("/api/skills/assessments")
def list_skill_assessments(
    athlete_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role_val = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role)
    q = db.query(SkillAssessment)
    if athlete_id:
        if not can_access_athlete(current_user, athlete_id, db):
            raise HTTPException(status_code=403, detail="Access denied.")
        q = q.filter(SkillAssessment.athlete_id == athlete_id)
    elif role_val == UserRole.ATHLETE.value:
        q = q.filter(SkillAssessment.athlete_id == current_user.id)

    rows = q.order_by(SkillAssessment.created_at.desc()).limit(50).all()
    users = {u.id: u.full_name for u in db.query(User).all()}
    return [_serialize_skill(r, users.get(r.athlete_id)) for r in rows]


# -------------------- GAMIFICATION --------------------


@router.get("/api/gamification/overview")
def gamification_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    evaluate_user_achievements(db, current_user.id)
    all_badges = db.query(Achievement).order_by(Achievement.points.asc()).all()
    earned_map = {
        ua.achievement_id: ua.earned_at.isoformat()
        for ua in db.query(UserAchievement).filter(UserAchievement.user_id == current_user.id).all()
    }
    badges = [
        {
            "id": b.id,
            "code": b.code,
            "name": b.name,
            "description": b.description,
            "icon": b.icon,
            "points": b.points,
            "category": b.category,
            "earned": b.id in earned_map,
            "earned_at": earned_map.get(b.id),
        }
        for b in all_badges
    ]

    leaderboard = build_leaderboard(db)
    my_entry = next((r for r in leaderboard if r["user_id"] == current_user.id), None)

    challenges = db.query(Challenge).filter(Challenge.is_active == True).order_by(Challenge.start_date.desc()).all()  # noqa: E712
    parts = {
        p.challenge_id: p
        for p in db.query(ChallengeParticipation)
        .filter(ChallengeParticipation.user_id == current_user.id)
        .all()
    }
    challenge_list = []
    for c in challenges:
        p = parts.get(c.id)
        progress_pct = (
            min(100.0, round((p.current_value / max(c.target_value, 1.0)) * 100.0, 1))
            if p
            else 0.0
        )
        challenge_list.append(
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "metric_type": c.metric_type,
                "target_value": c.target_value,
                "reward_points": c.reward_points,
                "reward_title": c.reward_title,
                "joined": p is not None,
                "current_value": p.current_value if p else 0.0,
                "progress_pct": progress_pct,
                "is_completed": p.is_completed if p else False,
            }
        )

    return {
        "user_summary": my_entry,
        "badges": badges,
        "leaderboard": leaderboard[:25],
        "challenges": challenge_list,
    }


@router.post("/api/gamification/challenges", status_code=status.HTTP_201_CREATED)
def create_challenge(
    payload: ChallengeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.COACH, UserRole.ANALYST)),
):
    ch = Challenge(created_by_id=current_user.id, **payload.model_dump())
    db.add(ch)
    db.commit()
    db.refresh(ch)
    log_activity(
        db,
        current_user.id,
        "challenge_created",
        "challenge",
        f"Created training challenge '{ch.title}' ({ch.target_value} {ch.metric_type}).",
        entity_id=ch.id,
    )
    return {
        "id": ch.id,
        "title": ch.title,
        "description": ch.description,
        "metric_type": ch.metric_type,
        "target_value": ch.target_value,
        "reward_points": ch.reward_points,
        "reward_title": ch.reward_title,
    }


@router.post("/api/gamification/challenges/{challenge_id}/join")
def join_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id, Challenge.is_active == True).first()  # noqa: E712
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found.")

    existing = (
        db.query(ChallengeParticipation)
        .filter(
            ChallengeParticipation.challenge_id == challenge_id,
            ChallengeParticipation.user_id == current_user.id,
        )
        .first()
    )
    if existing:
        return {"joined": True, "current_value": existing.current_value, "is_completed": existing.is_completed}

    part = ChallengeParticipation(challenge_id=challenge_id, user_id=current_user.id)
    db.add(part)
    db.commit()
    log_activity(
        db,
        current_user.id,
        "challenge_joined",
        "challenge",
        f"{current_user.full_name} joined challenge '{ch.title}'.",
        entity_id=ch.id,
    )
    return {"joined": True, "current_value": 0.0, "is_completed": False}


@router.post("/api/gamification/challenges/{challenge_id}/progress")
def update_challenge_progress(
    challenge_id: int,
    payload: ChallengeProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ch = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found.")

    part = (
        db.query(ChallengeParticipation)
        .filter(
            ChallengeParticipation.challenge_id == challenge_id,
            ChallengeParticipation.user_id == current_user.id,
        )
        .first()
    )
    if not part:
        part = ChallengeParticipation(challenge_id=challenge_id, user_id=current_user.id, current_value=0.0)
        db.add(part)

    part.current_value = round(part.current_value + payload.increment_value, 2)
    if part.current_value >= ch.target_value and not part.is_completed:
        part.is_completed = True
        part.completed_at = datetime.now(timezone.utc)
        log_activity(
            db,
            current_user.id,
            "challenge_completed",
            "challenge",
            f"{current_user.full_name} completed challenge '{ch.title}' (+{ch.reward_points} XP).",
            entity_id=ch.id,
        )

    db.commit()
    unlocked = evaluate_user_achievements(db, current_user.id)
    return {
        "challenge_id": ch.id,
        "current_value": part.current_value,
        "target_value": ch.target_value,
        "progress_pct": min(100.0, round((part.current_value / max(ch.target_value, 1.0)) * 100.0, 1)),
        "is_completed": part.is_completed,
        "newly_unlocked_badges": unlocked,
    }
