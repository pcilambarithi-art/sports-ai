import io
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.security import can_access_athlete, get_current_user
from app.db.database import get_db
from app.db.models import AIModelTrainingRun, AIPrediction, User, UserRole
from app.ml.coaching_ai_engine import coaching_ai_engine
from app.ml.model_service import ModelNotReadyError, model_service
from app.schemas.schemas import CaloriePredictionRequest
from app.services.activity_service import log_activity
from app.services.analytics_service import evaluate_user_achievements

router = APIRouter(prefix="/api/ml", tags=["Trained AI Model"])


def _serialize_prediction(p: AIPrediction, athlete_name: Optional[str] = None) -> dict:
    return {
        "id": p.id,
        "athlete_id": p.athlete_id,
        "athlete_name": athlete_name,
        "requested_by_id": p.requested_by_id,
        "inputs": {
            "Age": p.age,
            "Gender": p.gender,
            "Weight_KG": p.weight_kg,
            "Exercise_Type": p.exercise_type,
            "Duration_Minutes": p.duration_minutes,
            "Heart_Rate_BPM": p.heart_rate_bpm,
            "Workout_Frequency_Per_Week": p.workout_frequency_per_week,
            "Sleep_Hours": p.sleep_hours,
            "Water_Intake_Liters": p.water_intake_liters,
            "Fitness_Goal": p.fitness_goal,
            "Experience_Level": p.experience_level,
        },
        "predicted_calories": p.predicted_calories,
        "burn_rate_per_min": p.burn_rate_per_min,
        "ensemble_std": p.ensemble_std,
        "confidence_low": p.confidence_low,
        "confidence_high": p.confidence_high,
        "dataset_percentile": p.dataset_percentile,
        "explanation": p.explanation,
        "model_version": p.model_version,
        "created_at": p.created_at.isoformat(),
    }


@router.get("/status")
def get_model_status():
    """Return real status, file path, verified evaluation metrics, and limitations of the user's trained model."""
    status_data = model_service.get_status()
    status_data["companion_ai"] = coaching_ai_engine.metrics or {"ready": coaching_ai_engine.ready}
    return status_data


@router.get("/coaching-ai-status")
def get_coaching_ai_status(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    runs = (
        db.query(AIModelTrainingRun)
        .order_by(AIModelTrainingRun.created_at.desc())
        .limit(10)
        .all()
    )
    return {
        "metrics": coaching_ai_engine.metrics or {"ready": coaching_ai_engine.ready},
        "training_history": [
            {
                "id": r.id,
                "model_name": r.model_name,
                "dataset_rows_used": r.dataset_rows_used,
                "db_records_used": r.db_records_used,
                "knowledge_docs_used": r.knowledge_docs_used,
                "accuracy_pct": round(r.accuracy * 100.0, 2) if r.accuracy is not None else None,
                "macro_f1_pct": round(r.macro_f1 * 100.0, 2) if r.macro_f1 is not None else None,
                "cv_score_pct": round(r.cv_score * 100.0, 2) if r.cv_score is not None else None,
                "training_seconds": r.training_seconds,
                "created_at": r.created_at.isoformat(),
            }
            for r in runs
        ],
    }


@router.post("/train-coaching-ai")
def retrain_companion_coaching_ai(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Continuously train the companion Strain/Readiness Classifier & Semantic Coaching NLP AI
    on the 70k dataset + live database records + coaching knowledge base.
    Leaves D:\\V3\\trained_models\\calorie_prediction_model.pkl 100% untouched.
    """
    metrics = coaching_ai_engine.train_all(db, triggered_by_id=current_user.id)
    log_activity(
        db,
        current_user.id,
        "companion_ai_retrained",
        "ai_model",
        (
            f"Retrained Companion Coaching AI on {metrics['strain_classifier']['total_training_samples']:,} "
            f"samples ({metrics['strain_classifier']['test_accuracy_pct']}% acc) & "
            f"{metrics['semantic_coach_nlp']['knowledge_documents']} knowledge docs."
        ),
    )
    return metrics


@router.get("/benchmarks")
def get_dataset_benchmarks(_current_user: User = Depends(get_current_user)):
    """Return real summary statistics computed directly from D:\\V3\\preprocessed_workout_dataset.csv."""
    if not model_service.dataset_stats:
        return {"available": False, "message": "Dataset benchmark file not found or not loaded."}
    return {"available": True, **model_service.dataset_stats}


@router.post("/predict", status_code=status.HTTP_201_CREATED)
def predict_calories(
    payload: CaloriePredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_athlete_id = payload.athlete_id or current_user.id
    if not can_access_athlete(current_user, target_athlete_id, db):
        raise HTTPException(status_code=403, detail="Not permitted to run predictions for this athlete.")

    raw_input = {
        "Age": payload.Age,
        "Gender": payload.Gender,
        "Weight_KG": payload.Weight_KG,
        "Exercise_Type": payload.Exercise_Type,
        "Duration_Minutes": payload.Duration_Minutes,
        "Heart_Rate_BPM": payload.Heart_Rate_BPM,
        "Workout_Frequency_Per_Week": payload.Workout_Frequency_Per_Week,
        "Sleep_Hours": payload.Sleep_Hours,
        "Water_Intake_Liters": payload.Water_Intake_Liters,
        "Fitness_Goal": payload.Fitness_Goal,
        "Experience_Level": payload.Experience_Level,
    }

    try:
        result = model_service.predict_single(raw_input, include_what_if=payload.include_what_if)
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Model inference failed: {exc}",
        ) from exc

    record = AIPrediction(
        athlete_id=target_athlete_id,
        requested_by_id=current_user.id,
        age=payload.Age,
        gender=payload.Gender,
        weight_kg=payload.Weight_KG,
        exercise_type=payload.Exercise_Type,
        duration_minutes=payload.Duration_Minutes,
        heart_rate_bpm=payload.Heart_Rate_BPM,
        workout_frequency_per_week=payload.Workout_Frequency_Per_Week,
        sleep_hours=payload.Sleep_Hours,
        water_intake_liters=payload.Water_Intake_Liters,
        fitness_goal=payload.Fitness_Goal,
        experience_level=payload.Experience_Level,
        predicted_calories=result["predicted_calories"],
        burn_rate_per_min=result["burn_rate_per_min"],
        ensemble_std=result["ensemble_std"],
        confidence_low=result["confidence_low"],
        confidence_high=result["confidence_high"],
        dataset_percentile=result["dataset_percentile"],
        explanation=result["explanation"],
        model_version=result["model_version"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    athlete = db.query(User).filter(User.id == target_athlete_id).first()
    log_activity(
        db,
        current_user.id,
        "ai_prediction_created",
        "prediction",
        f"Predicted {record.predicted_calories:.1f} kcal for {payload.Exercise_Type} ({payload.Duration_Minutes:.0f} min @ {payload.Heart_Rate_BPM:.0f} BPM).",
        entity_id=record.id,
    )
    unlocked = evaluate_user_achievements(db, target_athlete_id)

    resp = _serialize_prediction(record, athlete.full_name if athlete else None)
    resp["ensemble_agreement_pct"] = result["ensemble_agreement_pct"]
    resp["exercise_benchmark"] = result["exercise_benchmark"]
    resp["strain_zone"] = coaching_ai_engine.predict_strain_zone(
        age=payload.Age,
        duration=payload.Duration_Minutes,
        hr=payload.Heart_Rate_BPM,
        freq=payload.Workout_Frequency_Per_Week,
        sleep=payload.Sleep_Hours,
        water=payload.Water_Intake_Liters,
        weight=payload.Weight_KG,
        predicted_calories=record.predicted_calories,
    )
    resp["newly_unlocked_badges"] = unlocked
    return resp


@router.post("/predict-batch")
async def predict_batch_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Run batch inference using the user's actual trained model on an uploaded CSV or Excel file."""
    filename = (file.filename or "").lower()
    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        raise HTTPException(status_code=400, detail="Only .csv, .xlsx, or .xls files are supported.")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Batch file exceeds 10 MB limit.")

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse uploaded file: {exc}") from exc

    if len(df) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file contains 0 rows.")
    if len(df) > 2000:
        raise HTTPException(status_code=400, detail="Batch upload limited to 2,000 rows per request.")

    try:
        rows = df.to_dict(orient="records")
        preds = model_service.predict_batch_fast(rows)
    except ModelNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Batch inference error: {exc}") from exc

    df["Predicted_Calories_Burned"] = preds
    return {
        "row_count": len(df),
        "mean_predicted_calories": round(float(pd.Series(preds).mean()), 2),
        "min_predicted_calories": round(float(pd.Series(preds).min()), 2),
        "max_predicted_calories": round(float(pd.Series(preds).max()), 2),
        "preview_rows": df.head(50).fillna("").to_dict(orient="records"),
    }


@router.get("/predictions")
def list_predictions(
    athlete_id: Optional[int] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role_val = current_user.role.value if isinstance(current_user.role, UserRole) else str(current_user.role)
    q = db.query(AIPrediction)
    if athlete_id:
        if not can_access_athlete(current_user, athlete_id, db):
            raise HTTPException(status_code=403, detail="Access denied.")
        q = q.filter(AIPrediction.athlete_id == athlete_id)
    elif role_val == UserRole.ATHLETE.value:
        q = q.filter(
            (AIPrediction.athlete_id == current_user.id)
            | (AIPrediction.requested_by_id == current_user.id)
        )

    rows = q.order_by(AIPrediction.created_at.desc()).limit(limit).all()
    users = {u.id: u.full_name for u in db.query(User).all()}
    return [_serialize_prediction(r, users.get(r.athlete_id)) for r in rows]


@router.get("/predictions/export")
def export_predictions_csv(
    athlete_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export real AI prediction history as CSV for third-party sports analytics tools."""
    data = list_predictions(athlete_id=athlete_id, limit=200, db=db, current_user=current_user)
    flat = []
    for item in data:
        row = {
            "id": item["id"],
            "athlete_name": item["athlete_name"],
            "created_at": item["created_at"],
            "predicted_calories": item["predicted_calories"],
            "burn_rate_per_min": item["burn_rate_per_min"],
            "confidence_low": item["confidence_low"],
            "confidence_high": item["confidence_high"],
            "dataset_percentile": item["dataset_percentile"],
            **item["inputs"],
        }
        flat.append(row)
    columns = [
        "id", "athlete_name", "created_at", "predicted_calories", "burn_rate_per_min",
        "confidence_low", "confidence_high", "dataset_percentile",
        "Age", "Gender", "Weight_KG", "Exercise_Type", "Duration_Minutes",
        "Heart_Rate_BPM", "Workout_Frequency_Per_Week", "Sleep_Hours",
        "Water_Intake_Liters", "Fitness_Goal", "Experience_Level",
    ]
    df = pd.DataFrame(flat, columns=columns) if not flat else pd.DataFrame(flat)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ai_predictions_export.csv"},
    )
