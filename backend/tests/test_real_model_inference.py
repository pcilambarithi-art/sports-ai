r"""
End-to-end live inference verification against the user's actual 2.93 GB
ExtraTreesRegressor model at D:\V3\trained_models\calorie_prediction_model.pkl.
"""

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.database import Base, get_db
from app.db.init_db import DEFAULT_ACHIEVEMENTS
from app.db.models import Achievement
from app.main import app
from app.ml.model_service import model_service


def test_real_trained_model_end_to_end_prediction(tmp_path: Path):
    test_engine = create_engine(
        f"sqlite:///{tmp_path / 'live_ml_test.db'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        for item in DEFAULT_ACHIEVEMENTS:
            db.add(Achievement(**item))
        db.commit()
    finally:
        db.close()

    def override_db():
        s = TestingSessionLocal()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_db
    try:
        model_service.initialize_metadata_and_benchmarks()
        model_service.load_sync()
        assert model_service.status == "ready", model_service.error_message

        with TestClient(app) as client:
            reg = client.post(
                "/api/auth/register",
                json={
                    "email": "mlverify@apexpulse.com",
                    "full_name": "ML Verification Athlete",
                    "password": "StrongPassword123!",
                    "role": "athlete",
                },
            )
            assert reg.status_code == 201
            token = reg.json()["access_token"]

            pred = client.post(
                "/api/ml/predict",
                json={
                    "Age": 28,
                    "Gender": "Male",
                    "Weight_KG": 75.0,
                    "Exercise_Type": "Running",
                    "Duration_Minutes": 45,
                    "Heart_Rate_BPM": 155,
                    "Workout_Frequency_Per_Week": 4,
                    "Sleep_Hours": 7.0,
                    "Water_Intake_Liters": 2.5,
                    "Fitness_Goal": "Weight Loss",
                    "Experience_Level": "Intermediate",
                    "include_what_if": True,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            assert pred.status_code == 201, pred.text
            body = pred.json()
            assert 200.0 <= body["predicted_calories"] <= 900.0
            assert body["confidence_low"] < body["predicted_calories"] < body["confidence_high"]
            assert body["dataset_percentile"] is not None
            assert len(body["explanation"]["what_if_scenarios"]) >= 2
            assert len(body["explanation"]["top_global_drivers"]) >= 5
    finally:
        app.dependency_overrides.clear()
        test_engine.dispose()
