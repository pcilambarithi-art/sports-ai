from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.ml.model_service import (
    VALID_EXERCISE_TYPES,
    VALID_EXPERIENCE_LEVELS,
    VALID_FITNESS_GOALS,
    VALID_GENDERS,
)


# -------------------- AUTH & USERS --------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=150)
    password: str = Field(..., min_length=8, max_length=128)
    role: Literal["admin", "coach", "analyst", "athlete"] = "athlete"
    sport: Optional[str] = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class AthleteProfileUpdate(BaseModel):
    sport: Optional[str] = Field(default=None, max_length=100)
    position: Optional[str] = Field(default=None, max_length=100)
    age: Optional[int] = Field(default=None, ge=10, le=100)
    gender: Optional[Literal["Male", "Female"]] = None
    weight_kg: Optional[float] = Field(default=None, gt=25, le=250)
    height_cm: Optional[float] = Field(default=None, gt=100, le=250)
    experience_level: Optional[Literal["Beginner", "Intermediate", "Advanced"]] = None
    fitness_goal: Optional[
        Literal["Endurance", "Flexibility", "General Fitness", "Muscle Gain", "Weight Loss"]
    ] = None
    preferred_exercise: Optional[
        Literal["Cycling", "HIIT", "Rowing", "Running", "Swimming", "Walking", "Weight Training", "Yoga"]
    ] = None
    workout_frequency_per_week: Optional[int] = Field(default=None, ge=1, le=7)
    avg_sleep_hours: Optional[float] = Field(default=None, ge=2.0, le=16.0)
    avg_water_intake_liters: Optional[float] = Field(default=None, ge=0.2, le=10.0)
    resting_heart_rate: Optional[int] = Field(default=None, ge=30, le=120)


class CoachProfileUpdate(BaseModel):
    specialization: Optional[str] = Field(default=None, max_length=150)
    certifications: Optional[str] = Field(default=None, max_length=1000)
    years_experience: Optional[int] = Field(default=None, ge=0, le=60)
    team_name: Optional[str] = Field(default=None, max_length=150)


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    bio: Optional[str] = Field(default=None, max_length=1000)
    athlete_profile: Optional[AthleteProfileUpdate] = None
    coach_profile: Optional[CoachProfileUpdate] = None


class AdminUserUpdate(BaseModel):
    role: Optional[Literal["admin", "coach", "analyst", "athlete"]] = None
    is_active: Optional[bool] = None


class AssignAthleteRequest(BaseModel):
    coach_id: int
    athlete_id: int
    notes: Optional[str] = Field(default=None, max_length=500)


# -------------------- AI MODEL PREDICTION --------------------


class CaloriePredictionRequest(BaseModel):
    athlete_id: Optional[int] = None
    Age: float = Field(..., ge=10, le=100)
    Gender: str
    Weight_KG: float = Field(..., gt=25, le=250)
    Exercise_Type: str
    Duration_Minutes: float = Field(..., gt=1, le=300)
    Heart_Rate_BPM: float = Field(..., ge=40, le=230)
    Workout_Frequency_Per_Week: float = Field(..., ge=1, le=7)
    Sleep_Hours: float = Field(..., ge=2.0, le=16.0)
    Water_Intake_Liters: float = Field(..., ge=0.2, le=10.0)
    Fitness_Goal: str
    Experience_Level: str
    include_what_if: bool = True

    @field_validator("Gender")
    @classmethod
    def check_gender(cls, v: str) -> str:
        match = next((g for g in VALID_GENDERS if g.lower() == v.strip().lower()), None)
        if not match:
            raise ValueError(f"Gender must be one of {VALID_GENDERS}")
        return match

    @field_validator("Exercise_Type")
    @classmethod
    def check_exercise(cls, v: str) -> str:
        match = next((e for e in VALID_EXERCISE_TYPES if e.lower() == v.strip().lower()), None)
        if not match:
            raise ValueError(f"Exercise_Type must be one of {VALID_EXERCISE_TYPES}")
        return match

    @field_validator("Fitness_Goal")
    @classmethod
    def check_goal(cls, v: str) -> str:
        match = next((g for g in VALID_FITNESS_GOALS if g.lower() == v.strip().lower()), None)
        if not match:
            raise ValueError(f"Fitness_Goal must be one of {VALID_FITNESS_GOALS}")
        return match

    @field_validator("Experience_Level")
    @classmethod
    def check_exp(cls, v: str) -> str:
        match = next((e for e in VALID_EXPERIENCE_LEVELS if e.lower() == v.strip().lower()), None)
        if not match:
            raise ValueError(f"Experience_Level must be one of {VALID_EXPERIENCE_LEVELS}")
        return match


# -------------------- PERFORMANCE RECORDS --------------------


class PerformanceRecordCreate(BaseModel):
    athlete_id: Optional[int] = None
    session_date: Optional[datetime] = None
    sport: Optional[str] = Field(default=None, max_length=80)
    exercise_type: str
    duration_minutes: float = Field(..., gt=1, le=360)
    heart_rate_bpm: float = Field(..., ge=40, le=230)
    speed_kmh: Optional[float] = Field(default=None, ge=0, le=80)
    distance_km: Optional[float] = Field(default=None, ge=0, le=300)
    calories_burned: Optional[float] = Field(default=None, ge=0, le=6000)
    rpe_score: Optional[int] = Field(default=None, ge=1, le=10)
    fatigue_level: Optional[int] = Field(default=None, ge=1, le=10)
    sleep_hours: Optional[float] = Field(default=None, ge=0, le=24)
    water_intake_liters: Optional[float] = Field(default=None, ge=0, le=15)
    notes: Optional[str] = Field(default=None, max_length=1000)
    auto_predict_calories: bool = True

    @field_validator("exercise_type")
    @classmethod
    def check_ex(cls, v: str) -> str:
        match = next((e for e in VALID_EXERCISE_TYPES if e.lower() == v.strip().lower()), None)
        if not match:
            raise ValueError(f"exercise_type must be one of {VALID_EXERCISE_TYPES}")
        return match


# -------------------- TRAINING PROGRAMS --------------------


class TrainingProgramGenerateRequest(BaseModel):
    athlete_id: Optional[int] = None
    title: Optional[str] = Field(default=None, max_length=200)
    sport: Optional[str] = Field(default=None, max_length=80)
    goal: Optional[str] = None
    experience_level: Optional[str] = None
    weekly_sessions: Optional[int] = Field(default=None, ge=2, le=7)


class SessionCompleteRequest(BaseModel):
    is_completed: bool = True
    feedback_rpe: Optional[int] = Field(default=None, ge=1, le=10)
    feedback_notes: Optional[str] = Field(default=None, max_length=500)


# -------------------- INJURY RISK --------------------


class InjuryRiskRunRequest(BaseModel):
    athlete_id: Optional[int] = None


# -------------------- OPPONENTS & STRATEGY --------------------


class OpponentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    sport: str = Field(..., min_length=2, max_length=80)
    team_or_club: Optional[str] = Field(default=None, max_length=150)
    avg_speed_kmh: Optional[float] = Field(default=None, ge=0, le=80)
    endurance_minutes: Optional[float] = Field(default=None, ge=0, le=400)
    win_rate_pct: Optional[float] = Field(default=None, ge=0, le=100)
    offensive_rating: Optional[float] = Field(default=None, ge=0, le=100)
    defensive_rating: Optional[float] = Field(default=None, ge=0, le=100)
    tempo_style: Optional[str] = Field(default=None, max_length=80)
    observed_strengths: Optional[str] = Field(default=None, max_length=1000)
    observed_weaknesses: Optional[str] = Field(default=None, max_length=1000)
    notes: Optional[str] = Field(default=None, max_length=1500)


class StrategyGenerateRequest(BaseModel):
    opponent_id: int
    athlete_id: Optional[int] = None
    title: Optional[str] = Field(default=None, max_length=200)
    tempo_adjustment_pct: float = Field(default=0.0, ge=-25.0, le=25.0)
    defensive_focus_pct: float = Field(default=50.0, ge=0.0, le=100.0)


# -------------------- REAL-TIME TELEMETRY --------------------


class TelemetryIngestRequest(BaseModel):
    athlete_id: Optional[int] = None
    source_type: Literal["wearable_webhook", "iot_sensor", "manual"] = "manual"
    device_name: Optional[str] = Field(default=None, max_length=120)
    heart_rate_bpm: Optional[float] = Field(default=None, ge=30, le=240)
    speed_kmh: Optional[float] = Field(default=None, ge=0, le=80)
    distance_km: Optional[float] = Field(default=None, ge=0, le=300)
    duration_minutes: Optional[float] = Field(default=None, ge=0, le=600)
    calories: Optional[float] = Field(default=None, ge=0, le=6000)
    muscle_load_pct: Optional[float] = Field(default=None, ge=0, le=100)
    fatigue_index: Optional[float] = Field(default=None, ge=0, le=10)


# -------------------- SKILL ASSESSMENT --------------------


class SkillAssessmentRunRequest(BaseModel):
    athlete_id: Optional[int] = None


# -------------------- GAMIFICATION --------------------


class ChallengeCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=5, max_length=1000)
    metric_type: Literal["calories", "sessions", "duration_minutes", "distance_km"]
    target_value: float = Field(..., gt=0)
    reward_points: int = Field(default=100, ge=10, le=5000)
    reward_title: Optional[str] = Field(default=None, max_length=120)


class ChallengeProgressUpdate(BaseModel):
    increment_value: float = Field(..., gt=0)


# -------------------- VIRTUAL COACHING ASSISTANT --------------------


class AssistantChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    athlete_id: Optional[int] = None


class CoachingKnowledgeCreate(BaseModel):
    category: str = Field(..., min_length=2, max_length=60)
    sport: str = Field(default="General", max_length=60)
    question_pattern: str = Field(..., min_length=5, max_length=300)
    answer: str = Field(..., min_length=10, max_length=3000)
    tags: Optional[str] = Field(default=None, max_length=255)
