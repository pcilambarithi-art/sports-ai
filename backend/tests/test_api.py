"""
Comprehensive integration tests for ApexPulse AI-Powered Sports Coaching System.

Covers:
- Auth (register/login/JWT) & RBAC enforcement across all 4 roles
- User profiles & coach-athlete assignments
- Existing trained ML model metadata, 70k dataset benchmarks & input validation
- Performance tracking & predictive trend forecasting
- Personalized training schedule generation, completion & adaptive adjustment
- Injury risk & workload anomaly detection + coach alert acknowledgement
- Opponent management & game strategy optimization
- Real-time telemetry ingestion (user + webhook API key) & sensor status
- Real OpenCV video upload, optical flow, contour tracking & keyframe serving
- Skill scoring, gamification badges, challenges & leaderboard
- Data-grounded Virtual Coaching Assistant
- Dashboard real-data integrity
"""

from __future__ import annotations

import os
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure isolated test DB and disable slow 2.93GB auto-load during fast unit suite
os.environ["AUTO_LOAD_MODEL"] = "false"

from app.core.config import settings
from app.db.database import Base, get_db
from app.db.init_db import init_db
from app.main import app


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("test_env")
    test_db_path = tmp_dir / "test_sports.db"
    test_upload_dir = tmp_dir / "uploads"
    settings.UPLOAD_DIR = str(test_upload_dir)

    # Isolate companion AI model artifacts inside pytest tmp_dir so production models are never overwritten
    import app.ml.coaching_ai_engine as cae
    orig_paths = (cae.COACHING_AI_DIR, cae.STRAIN_MODEL_PATH, cae.NLP_MODEL_PATH, cae.METRICS_JSON_PATH)
    cae.COACHING_AI_DIR = tmp_dir / "trained_coaching_ai"
    cae.STRAIN_MODEL_PATH = cae.COACHING_AI_DIR / "strain_readiness_classifier.pkl"
    cae.NLP_MODEL_PATH = cae.COACHING_AI_DIR / "coaching_nlp_assistant.pkl"
    cae.METRICS_JSON_PATH = cae.COACHING_AI_DIR / "coaching_ai_metrics.json"

    test_engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Seed static achievement badge catalog
    db = TestingSessionLocal()
    try:
        from app.db.init_db import DEFAULT_ACHIEVEMENTS
        from app.db.models import Achievement

        for item in DEFAULT_ACHIEVEMENTS:
            db.add(Achievement(**item))
        db.commit()
    finally:
        db.close()

    def override_get_db():
        s = TestingSessionLocal()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    cae.COACHING_AI_DIR, cae.STRAIN_MODEL_PATH, cae.NLP_MODEL_PATH, cae.METRICS_JSON_PATH = orig_paths
    test_engine.dispose()


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_test_video(path: Path) -> Path:
    """Create a genuine short MP4 video with a moving bright circle for real OpenCV testing."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, 15.0, (320, 240))
    for i in range(30):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        cx = 40 + i * 8
        cy = 120 + int(30 * np.sin(i / 4.0))
        cv2.circle(frame, (cx, cy), 22, (0, 220, 255), -1)
        writer.write(frame)
    writer.release()
    return path


def test_full_system_workflow(client: TestClient, tmp_path: Path):
    # 1. Health & ML Status (verifies metadata from D:\V3 without touching/retraining model)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    ml_status = client.get("/api/ml/status")
    assert ml_status.status_code == 200
    ms = ml_status.json()
    assert ms["algorithm"] == "Extra Trees Regressor"
    assert ms["n_estimators"] == 300
    assert ms["metrics"]["test_r2"] is not None

    # 2. Register users across all 4 roles
    athlete_reg = client.post(
        "/api/auth/register",
        json={
            "email": "athlete1@apexpulse.com",
            "full_name": "Jordan Rivera",
            "password": "StrongPassword123!",
            "role": "athlete",
            "sport": "Track & Field",
        },
    )
    assert athlete_reg.status_code == 201, athlete_reg.text
    athlete_token = athlete_reg.json()["access_token"]
    athlete_id = athlete_reg.json()["user"]["id"]

    coach_reg = client.post(
        "/api/auth/register",
        json={
            "email": "coach1@apexpulse.com",
            "full_name": "Coach Elena Vance",
            "password": "StrongPassword123!",
            "role": "coach",
            "sport": "Sprint & Endurance",
        },
    )
    assert coach_reg.status_code == 201, coach_reg.text
    coach_token = coach_reg.json()["access_token"]
    coach_id = coach_reg.json()["user"]["id"]

    admin_reg = client.post(
        "/api/auth/register",
        json={
            "email": "admin1@apexpulse.com",
            "full_name": "System Admin",
            "password": "StrongPassword123!",
            "role": "admin",
        },
    )
    assert admin_reg.status_code == 201, admin_reg.text
    admin_token = admin_reg.json()["access_token"]

    # RBAC check: athlete cannot call admin-only endpoint
    forbidden = client.patch(
        f"/api/users/{athlete_id}/admin",
        json={"role": "admin"},
        headers=_auth_header(athlete_token),
    )
    assert forbidden.status_code == 403

    # 3. Profile editing & Coach-Athlete assignment
    prof_res = client.put(
        "/api/users/me",
        json={
            "bio": "800m competitive runner",
            "athlete_profile": {
                "age": 24,
                "gender": "Male",
                "weight_kg": 72.5,
                "height_cm": 180,
                "experience_level": "Advanced",
                "fitness_goal": "Endurance",
                "preferred_exercise": "Running",
                "workout_frequency_per_week": 5,
                "avg_sleep_hours": 7.5,
                "avg_water_intake_liters": 3.0,
            },
        },
        headers=_auth_header(athlete_token),
    )
    assert prof_res.status_code == 200
    assert prof_res.json()["athlete_profile"]["weight_kg"] == 72.5

    assign_res = client.post(
        "/api/users/assignments",
        json={"coach_id": coach_id, "athlete_id": athlete_id, "notes": "Primary track coach"},
        headers=_auth_header(coach_token),
    )
    assert assign_res.status_code == 201

    # 4. Benchmarks from 70,000-row dataset & invalid input handling
    bench = client.get("/api/ml/benchmarks", headers=_auth_header(athlete_token))
    assert bench.status_code == 200
    assert bench.json()["available"] is True
    assert bench.json()["total_rows"] == 70000

    bad_pred = client.post(
        "/api/ml/predict",
        json={
            "Age": 25,
            "Gender": "InvalidGender",
            "Weight_KG": 75,
            "Exercise_Type": "Running",
            "Duration_Minutes": 40,
            "Heart_Rate_BPM": 150,
            "Workout_Frequency_Per_Week": 4,
            "Sleep_Hours": 7,
            "Water_Intake_Liters": 2.5,
            "Fitness_Goal": "Endurance",
            "Experience_Level": "Intermediate",
        },
        headers=_auth_header(athlete_token),
    )
    assert bad_pred.status_code == 422

    # 5. Performance logging (4 sessions) + Predictive Analytics Forecast
    for idx, (dur, hr, cal, rpe, fat) in enumerate(
        [(40, 148, 410, 6, 5), (50, 155, 530, 7, 6), (55, 162, 600, 8, 7), (75, 174, 820, 9, 8)]
    ):
        pr = client.post(
            "/api/performance",
            json={
                "exercise_type": "Running",
                "duration_minutes": dur,
                "heart_rate_bpm": hr,
                "speed_kmh": 13.5 + idx * 0.4,
                "distance_km": round(dur * 0.21, 2),
                "calories_burned": cal,
                "rpe_score": rpe,
                "fatigue_level": fat,
                "sleep_hours": 6.0 if idx == 3 else 7.5,
                "water_intake_liters": 2.2,
                "auto_predict_calories": False,
            },
            headers=_auth_header(athlete_token),
        )
        assert pr.status_code == 201

    forecast = client.get("/api/performance/forecast", headers=_auth_header(athlete_token))
    assert forecast.status_code == 200
    assert forecast.json()["available"] is True
    assert len(forecast.json()["forecast_points"]) == 8  # 4 actual + 4 forecast

    # 6. Personalized Training Program generation, completion & adaptation
    prog = client.post(
        "/api/training/generate",
        json={"goal": "Endurance", "experience_level": "Advanced", "weekly_sessions": 5},
        headers=_auth_header(athlete_token),
    )
    assert prog.status_code == 201
    prog_data = prog.json()
    assert len(prog_data["sessions"]) == 7

    first_session_id = prog_data["sessions"][0]["id"]
    comp = client.patch(
        f"/api/training/sessions/{first_session_id}/complete",
        json={"is_completed": True, "feedback_rpe": 9, "feedback_notes": "Tough threshold set"},
        headers=_auth_header(athlete_token),
    )
    assert comp.status_code == 200

    adapted = client.post(
        f"/api/training/programs/{prog_data['id']}/adapt",
        headers=_auth_header(athlete_token),
    )
    assert adapted.status_code == 200
    assert "RPE" in adapted.json()["adaptation_notes"]

    # 7. Injury Risk Assessment & Coach Alert Acknowledgement
    risk = client.post(
        "/api/injury/assess",
        json={"athlete_id": athlete_id},
        headers=_auth_header(coach_token),
    )
    assert risk.status_code == 201
    risk_data = risk.json()
    assert "NOT a medical diagnosis" in risk_data["disclaimer"]
    assert risk_data["risk_level"] in {"Low", "Moderate", "High"}

    ack = client.patch(
        f"/api/injury/assessments/{risk_data['id']}/acknowledge",
        headers=_auth_header(coach_token),
    )
    assert ack.status_code == 200
    assert ack.json()["coach_acknowledged"] is True

    # 8. Game Strategy & Opponent Optimization
    opp = client.post(
        "/api/strategy/opponents",
        json={
            "name": "Metro Striders Club",
            "sport": "Track & Field",
            "avg_speed_kmh": 14.2,
            "endurance_minutes": 48,
            "offensive_rating": 78,
            "defensive_rating": 65,
            "observed_strengths": "Fast opening splits",
            "observed_weaknesses": "Late-lap pace drop",
        },
        headers=_auth_header(coach_token),
    )
    assert opp.status_code == 201
    strat = client.post(
        "/api/strategy/generate",
        json={
            "opponent_id": opp.json()["id"],
            "athlete_id": athlete_id,
            "tempo_adjustment_pct": 5.0,
            "defensive_focus_pct": 55.0,
        },
        headers=_auth_header(coach_token),
    )
    assert strat.status_code == 201
    assert len(strat.json()["counter_strategies"]) >= 2
    assert len(strat.json()["scenario_simulations"]) == 3

    # 9. Real-Time Telemetry Status (honestly reports awaiting sensor before webhook)
    t_status_before = client.get("/api/telemetry/status", headers=_auth_header(athlete_token))
    assert t_status_before.status_code == 200
    assert t_status_before.json()["hardware_connected"] is False
    assert "Awaiting" in t_status_before.json()["status_label"]

    # Ingest via external sensor webhook API key
    wh = client.post(
        "/api/telemetry/webhook",
        json={
            "athlete_id": athlete_id,
            "source_type": "wearable_webhook",
            "device_name": "Polar H10 Chest Strap",
            "heart_rate_bpm": 154,
            "speed_kmh": 14.1,
            "distance_km": 6.2,
            "duration_minutes": 26,
            "calories": 310,
        },
        headers={"X-Sensor-API-Key": settings.SENSOR_API_KEY},
    )
    assert wh.status_code == 201

    t_status_after = client.get("/api/telemetry/status", headers=_auth_header(athlete_token))
    assert t_status_after.json()["hardware_connected"] is True

    # 10. Real OpenCV Video Analysis & Keyframe Serving
    video_file = _create_test_video(tmp_path / "sprint_drill.mp4")
    with open(video_file, "rb") as f:
        vid_res = client.post(
            "/api/video/analyze",
            files={"file": ("sprint_drill.mp4", f, "video/mp4")},
            data={"sport": "Track & Field", "exercise_type": "Running", "run_calorie_model": "false"},
            headers=_auth_header(athlete_token),
        )
    assert vid_res.status_code == 201
    vid_data = vid_res.json()
    assert vid_data["frame_count"] == 30
    assert vid_data["peak_motion_intensity"] > 0
    assert len(vid_data["key_moments"]) >= 1

    kf_url = vid_data["key_moments"][0]["image_url"]
    kf_res = client.get(kf_url)
    assert kf_res.status_code == 200
    assert kf_res.headers["content-type"] == "image/png"

    # 11. Skill Assessment & Gamification
    skill = client.post(
        "/api/skills/assess",
        json={"athlete_id": athlete_id},
        headers=_auth_header(athlete_token),
    )
    assert skill.status_code == 201
    assert 0 <= skill.json()["overall_score"] <= 100

    ch = client.post(
        "/api/gamification/challenges",
        json={
            "title": "10K Weekly Volume",
            "description": "Accumulate 10 km in training this week.",
            "metric_type": "distance_km",
            "target_value": 10.0,
            "reward_points": 150,
            "reward_title": "Road Warrior",
        },
        headers=_auth_header(coach_token),
    )
    assert ch.status_code == 201
    ch_id = ch.json()["id"]

    assert client.post(f"/api/gamification/challenges/{ch_id}/join", headers=_auth_header(athlete_token)).status_code == 200
    prog_up = client.post(
        f"/api/gamification/challenges/{ch_id}/progress",
        json={"increment_value": 12.0},
        headers=_auth_header(athlete_token),
    )
    assert prog_up.status_code == 200
    assert prog_up.json()["is_completed"] is True

    gam = client.get("/api/gamification/overview", headers=_auth_header(athlete_token))
    assert gam.status_code == 200
    assert gam.json()["user_summary"]["total_points"] > 0

    # 12. Virtual Coaching Assistant + Trained Semantic NLP + Knowledge Base + Companion AI Retraining
    kb_add = client.post(
        "/api/assistant/knowledge",
        json={
            "category": "strategy",
            "sport": "Track & Field",
            "question_pattern": "How should 800m runners pace the first 400m split?",
            "answer": "Run a controlled 1.5-2 second positive split on the opening 400m to stay relaxed without crossing early anaerobic threshold.",
            "tags": "800m,pacing,splits,track",
        },
        headers=_auth_header(coach_token),
    )
    assert kb_add.status_code == 201

    chat = client.post(
        "/api/assistant/chat",
        json={"message": "Give me a summary of my performance report, training schedule, and how 800m runners pace the first 400m split."},
        headers=_auth_header(athlete_token),
    )
    assert chat.status_code == 200
    assert "Training Plan" in chat.json()["reply"]
    assert "Performance Summary" in chat.json()["reply"]
    assert "AI Coaching Knowledge" in chat.json()["reply"]

    ai_status = client.get("/api/ml/coaching-ai-status", headers=_auth_header(admin_token))
    assert ai_status.status_code == 200
    assert ai_status.json()["metrics"]["strain_classifier"]["test_accuracy_pct"] >= 90.0

    # 13. Dashboard real DB metrics
    dash = client.get("/api/dashboard/overview", headers=_auth_header(admin_token))
    assert dash.status_code == 200
    kpis = dash.json()["kpis"]
    assert kpis["total_athletes"] == 1
    assert kpis["active_coaches"] == 1
    assert kpis["training_sessions"] == 4
    assert kpis["video_analyses"] == 1
