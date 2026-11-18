import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import can_access_athlete, get_current_user
from app.cv.video_analyzer import ALLOWED_VIDEO_EXTENSIONS, analyze_sports_video
from app.db.database import get_db
from app.db.models import AIPrediction, AthleteProfile, User, UserRole, VideoAnalysis
from app.ml.model_service import VALID_EXERCISE_TYPES, model_service
from app.services.activity_service import log_activity
from app.services.analytics_service import _safe_athlete_defaults, evaluate_user_achievements

router = APIRouter(prefix="/api/video", tags=["Video Analysis & OpenCV Feedback"])


def _serialize_video_analysis(v: VideoAnalysis, athlete_name: Optional[str] = None, linked_pred: Optional[AIPrediction] = None) -> dict:
    moments = []
    for m in v.key_moments or []:
        m_copy = dict(m)
        if m_copy.get("image_filename"):
            m_copy["image_url"] = f"/api/video/keyframes/{v.id}/{m_copy['image_filename']}"
        moments.append(m_copy)

    return {
        "id": v.id,
        "athlete_id": v.athlete_id,
        "athlete_name": athlete_name,
        "original_filename": v.original_filename,
        "sport": v.sport,
        "exercise_type": v.exercise_type,
        "duration_seconds": v.duration_seconds,
        "fps": v.fps,
        "frame_count": v.frame_count,
        "resolution": v.resolution,
        "mean_motion_intensity": v.mean_motion_intensity,
        "peak_motion_intensity": v.peak_motion_intensity,
        "active_movement_ratio_pct": v.active_movement_ratio_pct,
        "motion_timeline": v.motion_timeline or [],
        "trajectory_points": v.trajectory_points or [],
        "key_moments": moments,
        "feedback_items": v.feedback_items or [],
        "linked_prediction": (
            {
                "id": linked_pred.id,
                "predicted_calories": linked_pred.predicted_calories,
                "burn_rate_per_min": linked_pred.burn_rate_per_min,
                "exercise_type": linked_pred.exercise_type,
                "duration_minutes": linked_pred.duration_minutes,
                "heart_rate_bpm": linked_pred.heart_rate_bpm,
            }
            if linked_pred
            else None
        ),
        "analysis_disclaimer": v.analysis_disclaimer,
        "created_at": v.created_at.isoformat(),
    }


@router.post("/analyze", status_code=status.HTTP_201_CREATED)
async def upload_and_analyze_video(
    file: UploadFile = File(...),
    athlete_id: Optional[int] = Form(default=None),
    sport: Optional[str] = Form(default=None),
    exercise_type: Optional[str] = Form(default=None),
    heart_rate_bpm: Optional[float] = Form(default=None),
    session_duration_minutes: Optional[float] = Form(default=None),
    run_calorie_model: bool = Form(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_id = athlete_id or current_user.id
    if not can_access_athlete(current_user, target_id, db):
        raise HTTPException(status_code=403, detail="Access denied for this athlete.")

    orig_name = Path(file.filename or "video.mp4").name
    ext = Path(orig_name).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format '{ext}'. Allowed: {sorted(ALLOWED_VIDEO_EXTENSIONS)}",
        )

    max_bytes = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded video file is empty.")
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Video exceeds {settings.MAX_VIDEO_SIZE_MB} MB upload limit.",
        )

    analysis_uuid = uuid.uuid4().hex[:12]
    video_dir = settings.upload_path / "videos" / analysis_uuid
    video_dir.mkdir(parents=True, exist_ok=True)
    saved_video_path = video_dir / f"source{ext}"
    saved_video_path.write_bytes(content)

    frames_dir = video_dir / "keyframes"
    try:
        cv_result = analyze_sports_video(saved_video_path, frames_dir)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"OpenCV video processing failed: {exc}") from exc

    # Optional: invoke user's trained calorie model ONLY when compatible workout metrics are supplied & model is ready
    linked_pred: Optional[AIPrediction] = None
    if run_calorie_model and model_service.status == "ready" and exercise_type in VALID_EXERCISE_TYPES:
        profile = db.query(AthleteProfile).filter(AthleteProfile.user_id == target_id).first()
        defaults = _safe_athlete_defaults(profile)
        dur_min = session_duration_minutes or max(15.0, round(cv_result["duration_seconds"] / 60.0, 2))
        hr = heart_rate_bpm or 145.0
        raw = dict(defaults)
        raw["Exercise_Type"] = exercise_type
        raw["Duration_Minutes"] = dur_min
        raw["Heart_Rate_BPM"] = hr
        try:
            res = model_service.predict_single(raw, include_what_if=False)
            linked_pred = AIPrediction(
                athlete_id=target_id,
                requested_by_id=current_user.id,
                age=raw["Age"],
                gender=raw["Gender"],
                weight_kg=raw["Weight_KG"],
                exercise_type=exercise_type,
                duration_minutes=dur_min,
                heart_rate_bpm=hr,
                workout_frequency_per_week=raw["Workout_Frequency_Per_Week"],
                sleep_hours=raw["Sleep_Hours"],
                water_intake_liters=raw["Water_Intake_Liters"],
                fitness_goal=raw["Fitness_Goal"],
                experience_level=raw["Experience_Level"],
                predicted_calories=res["predicted_calories"],
                burn_rate_per_min=res["burn_rate_per_min"],
                ensemble_std=res["ensemble_std"],
                confidence_low=res["confidence_low"],
                confidence_high=res["confidence_high"],
                dataset_percentile=res["dataset_percentile"],
                explanation=res["explanation"],
                model_version=res["model_version"],
            )
            db.add(linked_pred)
            db.flush()
        except Exception:
            linked_pred = None

    record = VideoAnalysis(
        athlete_id=target_id,
        uploaded_by_id=current_user.id,
        original_filename=orig_name,
        stored_video_path=str(saved_video_path),
        sport=sport,
        exercise_type=exercise_type,
        duration_seconds=cv_result["duration_seconds"],
        fps=cv_result["fps"],
        frame_count=cv_result["frame_count"],
        resolution=cv_result["resolution"],
        mean_motion_intensity=cv_result["mean_motion_intensity"],
        peak_motion_intensity=cv_result["peak_motion_intensity"],
        active_movement_ratio_pct=cv_result["active_movement_ratio_pct"],
        motion_timeline=cv_result["motion_timeline"],
        trajectory_points=cv_result["trajectory_points"],
        key_moments=cv_result["key_moments"],
        feedback_items=cv_result["feedback_items"],
        linked_prediction_id=linked_pred.id if linked_pred else None,
        analysis_disclaimer=cv_result["analysis_disclaimer"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    athlete = db.query(User).filter(User.id == target_id).first()
    log_activity(
        db,
        current_user.id,
        "video_analyzed",
        "video_analysis",
        f"Analyzed video '{orig_name}' via OpenCV ({record.duration_seconds:.1f}s, {record.active_movement_ratio_pct}% active motion).",
        entity_id=record.id,
    )
    unlocked = evaluate_user_achievements(db, target_id)
    out = _serialize_video_analysis(record, athlete.full_name if athlete else None, linked_pred)
    out["newly_unlocked_badges"] = unlocked
    return out


@router.get("/analyses")
def list_video_analyses(
    athlete_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role_val = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role)
    q = db.query(VideoAnalysis)
    if athlete_id:
        if not can_access_athlete(current_user, athlete_id, db):
            raise HTTPException(status_code=403, detail="Access denied.")
        q = q.filter(VideoAnalysis.athlete_id == athlete_id)
    elif role_val == UserRole.ATHLETE.value:
        q = q.filter(
            (VideoAnalysis.athlete_id == current_user.id)
            | (VideoAnalysis.uploaded_by_id == current_user.id)
        )

    rows = q.order_by(VideoAnalysis.created_at.desc()).limit(30).all()
    users = {u.id: u.full_name for u in db.query(User).all()}
    pred_ids = [r.linked_prediction_id for r in rows if r.linked_prediction_id]
    preds = (
        {p.id: p for p in db.query(AIPrediction).filter(AIPrediction.id.in_(pred_ids)).all()}
        if pred_ids
        else {}
    )
    return [_serialize_video_analysis(r, users.get(r.athlete_id), preds.get(r.linked_prediction_id)) for r in rows]


@router.get("/keyframes/{analysis_id}/{filename}")
def get_keyframe_image(
    analysis_id: int,
    filename: str,
    db: Session = Depends(get_db),
):
    """Serve generated OpenCV annotated keyframe PNG safely (prevents path traversal)."""
    safe_name = Path(filename).name
    if safe_name != filename or not safe_name.endswith(".png"):
        raise HTTPException(status_code=400, detail="Invalid keyframe filename.")
    record = db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Video analysis not found.")

    frame_path = Path(record.stored_video_path).parent / "keyframes" / safe_name
    if not frame_path.exists():
        raise HTTPException(status_code=404, detail="Keyframe image not found.")
    return FileResponse(frame_path, media_type="image/png")
