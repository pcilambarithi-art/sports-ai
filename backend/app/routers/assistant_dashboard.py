from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import can_access_athlete, get_current_user
from app.db.database import get_db
from app.db.models import (
    AIPrediction,
    ActivityLog,
    ChatMessage,
    CoachingKnowledge,
    InjuryRiskAssessment,
    PerformanceRecord,
    TrainingProgram,
    TrainingSession,
    User,
    UserRole,
    VideoAnalysis,
)
from app.ml.coaching_ai_engine import coaching_ai_engine
from app.ml.model_service import model_service
from app.schemas.schemas import AssistantChatRequest, CoachingKnowledgeCreate
from app.services.activity_service import log_activity
from app.services.analytics_service import generate_assistant_reply

router = APIRouter(tags=["Virtual Coaching Assistant & Dashboard"])


@router.post("/api/assistant/chat")
def assistant_chat(
    payload: AssistantChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.athlete_id and not can_access_athlete(current_user, payload.athlete_id, db):
        raise HTTPException(status_code=403, detail="Access denied for selected athlete context.")

    user_msg = ChatMessage(
        user_id=current_user.id,
        athlete_context_id=payload.athlete_id or current_user.id,
        sender="user",
        message=payload.message.strip(),
    )
    db.add(user_msg)
    db.flush()

    reply_data = generate_assistant_reply(
        db=db,
        current_user=current_user,
        athlete_id=payload.athlete_id,
        user_message=payload.message,
    )

    bot_msg = ChatMessage(
        user_id=current_user.id,
        athlete_context_id=reply_data["athlete_id"],
        sender="assistant",
        message=reply_data["reply"],
        metadata_json={"sources": reply_data["sources"]},
    )
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)

    return {
        "id": bot_msg.id,
        "reply": bot_msg.message,
        "sources": reply_data["sources"],
        "athlete_id": reply_data["athlete_id"],
        "athlete_name": reply_data["athlete_name"],
        "created_at": bot_msg.created_at.isoformat(),
    }


@router.get("/api/assistant/history")
def assistant_history(
    limit: int = Query(default=40, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "sender": r.sender,
            "message": r.message,
            "sources": (r.metadata_json or {}).get("sources", []),
            "created_at": r.created_at.isoformat(),
        }
        for r in reversed(rows)
    ]


@router.get("/api/assistant/knowledge")
def list_coaching_knowledge(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    rows = db.query(CoachingKnowledge).order_by(CoachingKnowledge.id.desc()).limit(100).all()
    return [
        {
            "id": r.id,
            "category": r.category,
            "sport": r.sport,
            "question_pattern": r.question_pattern,
            "answer": r.answer,
            "tags": r.tags,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.post("/api/assistant/knowledge", status_code=201)
def add_coaching_knowledge(
    payload: CoachingKnowledgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add custom team/sport coaching knowledge into the DB and retrain the Semantic Coaching AI."""
    item = CoachingKnowledge(
        category=payload.category.strip().lower().replace(" ", "_"),
        sport=payload.sport.strip(),
        question_pattern=payload.question_pattern.strip(),
        answer=payload.answer.strip(),
        tags=payload.tags.strip() if payload.tags else None,
        created_by_id=current_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    metrics = coaching_ai_engine.train_all(db, triggered_by_id=current_user.id)
    log_activity(
        db,
        current_user.id,
        "knowledge_added",
        "coaching_knowledge",
        f"Added coaching knowledge ({item.sport} · {item.category}) and retrained Coaching AI.",
        entity_id=item.id,
    )
    return {
        "id": item.id,
        "category": item.category,
        "sport": item.sport,
        "question_pattern": item.question_pattern,
        "answer": item.answer,
        "retrained_metrics": metrics["semantic_coach_nlp"],
    }


@router.get("/api/dashboard/overview")
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Comprehensive dashboard derived strictly from real database records and verified model metrics."""
    role_val = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role)
    is_athlete_only = role_val == UserRole.ATHLETE.value

    total_athletes = db.query(User).filter(User.role == UserRole.ATHLETE, User.is_active == True).count()  # noqa: E712
    active_coaches = db.query(User).filter(User.role == UserRole.COACH, User.is_active == True).count()  # noqa: E712

    perf_q = db.query(PerformanceRecord)
    pred_q = db.query(AIPrediction)
    vid_q = db.query(VideoAnalysis)
    risk_q = db.query(InjuryRiskAssessment)
    prog_q = db.query(TrainingProgram)

    if is_athlete_only:
        perf_q = perf_q.filter(PerformanceRecord.athlete_id == current_user.id)
        pred_q = pred_q.filter(
            (AIPrediction.athlete_id == current_user.id) | (AIPrediction.requested_by_id == current_user.id)
        )
        vid_q = vid_q.filter(
            (VideoAnalysis.athlete_id == current_user.id) | (VideoAnalysis.uploaded_by_id == current_user.id)
        )
        risk_q = risk_q.filter(InjuryRiskAssessment.athlete_id == current_user.id)
        prog_q = prog_q.filter(TrainingProgram.athlete_id == current_user.id)

    total_sessions = perf_q.count()
    total_predictions = pred_q.count()
    total_videos = vid_q.count()

    avg_q = db.query(func.avg(AIPrediction.predicted_calories))
    if is_athlete_only:
        avg_q = avg_q.filter(
            (AIPrediction.athlete_id == current_user.id)
            | (AIPrediction.requested_by_id == current_user.id)
        )
    avg_pred_cals = avg_q.scalar()

    recent_perf = perf_q.order_by(PerformanceRecord.session_date.desc()).limit(10).all()
    recent_preds = pred_q.order_by(AIPrediction.created_at.desc()).limit(6).all()
    recent_videos = vid_q.order_by(VideoAnalysis.created_at.desc()).limit(4).all()
    alerts = (
        risk_q.filter(InjuryRiskAssessment.coach_alert_required == True)  # noqa: E712
        .order_by(InjuryRiskAssessment.created_at.desc())
        .limit(6)
        .all()
    )

    programs = prog_q.filter(TrainingProgram.status == "active").all()
    total_plan_sessions = 0
    completed_plan_sessions = 0
    for p in programs:
        s_list = db.query(TrainingSession).filter(TrainingSession.program_id == p.id).all()
        total_plan_sessions += len(s_list)
        completed_plan_sessions += sum(1 for s in s_list if s.is_completed)

    act_q = db.query(ActivityLog)
    if is_athlete_only:
        act_q = act_q.filter(ActivityLog.user_id == current_user.id)
    recent_activities = act_q.order_by(ActivityLog.created_at.desc()).limit(12).all()

    users = {u.id: u.full_name for u in db.query(User).all()}

    return {
        "kpis": {
            "total_athletes": total_athletes,
            "active_coaches": active_coaches,
            "training_sessions": total_sessions,
            "ai_predictions": total_predictions,
            "video_analyses": total_videos,
            "avg_predicted_calories": round(float(avg_pred_cals), 1) if avg_pred_cals is not None else None,
            "active_injury_alerts": sum(1 for a in alerts if not a.coach_acknowledged),
            "training_plan_completion_pct": (
                round((completed_plan_sessions / total_plan_sessions) * 100.0, 1)
                if total_plan_sessions > 0
                else None
            ),
        },
        "model_summary": {
            "status": model_service.status,
            "ready": model_service.status == "ready",
            "algorithm": model_service.model_features.get("algorithm", "Extra Trees Regressor"),
            "test_r2_pct": (
                round(float(model_service.model_features["test_r2"]) * 100, 2)
                if "test_r2" in model_service.model_features
                else None
            ),
            "test_mae": (
                round(float(model_service.model_features["test_mae"]), 2)
                if "test_mae" in model_service.model_features
                else None
            ),
        },
        "performance_trend": [
            {
                "date": r.session_date.strftime("%b %d"),
                "exercise_type": r.exercise_type,
                "duration_minutes": r.duration_minutes,
                "heart_rate_bpm": r.heart_rate_bpm,
                "calories": r.calories_burned or r.ai_predicted_calories or 0,
            }
            for r in reversed(recent_perf)
        ],
        "recent_predictions": [
            {
                "id": p.id,
                "athlete_name": users.get(p.athlete_id, "Unknown"),
                "exercise_type": p.exercise_type,
                "duration_minutes": p.duration_minutes,
                "heart_rate_bpm": p.heart_rate_bpm,
                "predicted_calories": p.predicted_calories,
                "burn_rate_per_min": p.burn_rate_per_min,
                "created_at": p.created_at.isoformat(),
            }
            for p in recent_preds
        ],
        "recent_videos": [
            {
                "id": v.id,
                "original_filename": v.original_filename,
                "duration_seconds": v.duration_seconds,
                "active_movement_ratio_pct": v.active_movement_ratio_pct,
                "peak_motion_intensity": v.peak_motion_intensity,
                "created_at": v.created_at.isoformat(),
            }
            for v in recent_videos
        ],
        "injury_alerts": [
            {
                "id": a.id,
                "athlete_id": a.athlete_id,
                "athlete_name": users.get(a.athlete_id, "Unknown"),
                "risk_score": a.risk_score,
                "risk_level": a.risk_level,
                "acwr": a.acwr,
                "coach_acknowledged": a.coach_acknowledged,
                "top_factor": (a.risk_factors[0] if a.risk_factors else "Workload threshold triggered."),
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ],
        "recent_activities": [
            {
                "id": a.id,
                "action": a.action,
                "entity_type": a.entity_type,
                "summary": a.summary,
                "created_at": a.created_at.isoformat(),
            }
            for a in recent_activities
        ],
    }
