import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    COACH = "coach"
    ANALYST = "analyst"
    ATHLETE = "athlete"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.ATHLETE, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    avatar_initials = Column(String(4), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    athlete_profile = relationship(
        "AthleteProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    coach_profile = relationship(
        "CoachProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class AthleteProfile(Base):
    __tablename__ = "athlete_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    sport = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)  # Male / Female
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    experience_level = Column(String(30), nullable=True)  # Beginner / Intermediate / Advanced
    fitness_goal = Column(String(50), nullable=True)  # Endurance / Flexibility / General Fitness / Muscle Gain / Weight Loss
    preferred_exercise = Column(String(50), nullable=True)
    workout_frequency_per_week = Column(Integer, nullable=True)
    avg_sleep_hours = Column(Float, nullable=True)
    avg_water_intake_liters = Column(Float, nullable=True)
    resting_heart_rate = Column(Integer, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="athlete_profile")


class CoachProfile(Base):
    __tablename__ = "coach_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialization = Column(String(150), nullable=True)
    certifications = Column(Text, nullable=True)
    years_experience = Column(Integer, nullable=True)
    team_name = Column(String(150), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="coach_profile")


class CoachAthleteLink(Base):
    __tablename__ = "coach_athlete_links"
    __table_args__ = (UniqueConstraint("coach_id", "athlete_id", name="uq_coach_athlete"),)

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    athlete_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    notes = Column(Text, nullable=True)


class AIPrediction(Base):
    __tablename__ = "ai_predictions"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    requested_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    # Exact raw features passed to the trained model
    age = Column(Float, nullable=False)
    gender = Column(String(20), nullable=False)
    weight_kg = Column(Float, nullable=False)
    exercise_type = Column(String(50), nullable=False, index=True)
    duration_minutes = Column(Float, nullable=False)
    heart_rate_bpm = Column(Float, nullable=False)
    workout_frequency_per_week = Column(Float, nullable=False)
    sleep_hours = Column(Float, nullable=False)
    water_intake_liters = Column(Float, nullable=False)
    fitness_goal = Column(String(50), nullable=False)
    experience_level = Column(String(30), nullable=False)

    # Real outputs from the trained ExtraTreesRegressor
    predicted_calories = Column(Float, nullable=False)
    burn_rate_per_min = Column(Float, nullable=False)
    ensemble_std = Column(Float, nullable=True)
    confidence_low = Column(Float, nullable=True)
    confidence_high = Column(Float, nullable=True)
    dataset_percentile = Column(Float, nullable=True)
    explanation = Column(JSON, nullable=True)
    model_version = Column(String(120), nullable=False, default="ExtraTreesRegressor-300-D-V3")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class PerformanceRecord(Base):
    __tablename__ = "performance_records"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    logged_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_date = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    sport = Column(String(80), nullable=True)
    exercise_type = Column(String(50), nullable=False)
    duration_minutes = Column(Float, nullable=False)
    heart_rate_bpm = Column(Float, nullable=False)
    speed_kmh = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=True)
    calories_burned = Column(Float, nullable=True)
    ai_predicted_calories = Column(Float, nullable=True)
    rpe_score = Column(Integer, nullable=True)  # 1-10 Rate of Perceived Exertion
    fatigue_level = Column(Integer, nullable=True)  # 1-10
    sleep_hours = Column(Float, nullable=True)
    water_intake_liters = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class TrainingProgram(Base):
    __tablename__ = "training_programs"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(200), nullable=False)
    sport = Column(String(80), nullable=True)
    goal = Column(String(80), nullable=False)
    experience_level = Column(String(40), nullable=False)
    weekly_target_sessions = Column(Integer, nullable=False, default=4)
    weekly_target_calories = Column(Float, nullable=True)
    status = Column(String(30), nullable=False, default="active")  # active / completed / archived
    adaptation_notes = Column(Text, nullable=True)
    generated_by_ai = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    sessions = relationship(
        "TrainingSession", back_populates="program", cascade="all, delete-orphan"
    )


class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("training_programs.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(String(20), nullable=False)  # Monday..Sunday
    day_index = Column(Integer, nullable=False)  # 1..7
    exercise_type = Column(String(50), nullable=False)
    focus_area = Column(String(120), nullable=False)
    target_duration_minutes = Column(Float, nullable=False)
    target_heart_rate_bpm = Column(Float, nullable=False)
    expected_calories = Column(Float, nullable=True)  # from trained ML model when ready
    intensity = Column(String(30), nullable=False)  # Low / Moderate / High / Recovery
    instructions = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    feedback_rpe = Column(Integer, nullable=True)
    feedback_notes = Column(Text, nullable=True)

    program = relationship("TrainingProgram", back_populates="sessions")


class InjuryRiskAssessment(Base):
    __tablename__ = "injury_risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assessed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    risk_score = Column(Float, nullable=False)  # 0-100 rule-based workload risk index
    risk_level = Column(String(20), nullable=False)  # Low / Moderate / High
    acute_load_7d = Column(Float, nullable=False)
    chronic_load_28d = Column(Float, nullable=False)
    acwr = Column(Float, nullable=True)  # Acute:Chronic Workload Ratio
    anomalies_detected = Column(JSON, nullable=False, default=list)
    risk_factors = Column(JSON, nullable=False, default=list)
    preventive_exercises = Column(JSON, nullable=False, default=list)
    training_modifications = Column(JSON, nullable=False, default=list)
    coach_alert_required = Column(Boolean, default=False, nullable=False)
    coach_acknowledged = Column(Boolean, default=False, nullable=False)
    disclaimer = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class Opponent(Base):
    __tablename__ = "opponents"

    id = Column(Integer, primary_key=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(150), nullable=False, index=True)
    sport = Column(String(80), nullable=False)
    team_or_club = Column(String(150), nullable=True)
    # Optional user-provided verified stats (null = data unavailable, never fabricated)
    avg_speed_kmh = Column(Float, nullable=True)
    endurance_minutes = Column(Float, nullable=True)
    win_rate_pct = Column(Float, nullable=True)
    offensive_rating = Column(Float, nullable=True)  # 0-100 user-entered
    defensive_rating = Column(Float, nullable=True)  # 0-100 user-entered
    tempo_style = Column(String(80), nullable=True)
    observed_strengths = Column(Text, nullable=True)
    observed_weaknesses = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    strategies = relationship(
        "GameStrategy", back_populates="opponent", cascade="all, delete-orphan"
    )


class GameStrategy(Base):
    __tablename__ = "game_strategies"

    id = Column(Integer, primary_key=True, index=True)
    opponent_id = Column(Integer, ForeignKey("opponents.id", ondelete="CASCADE"), nullable=False, index=True)
    athlete_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(200), nullable=False)
    tactical_summary = Column(Text, nullable=False)
    counter_strategies = Column(JSON, nullable=False, default=list)
    comparison_metrics = Column(JSON, nullable=False, default=dict)
    scenario_simulations = Column(JSON, nullable=False, default=list)
    data_availability_notes = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    opponent = relationship("Opponent", back_populates="strategies")


class TelemetryReading(Base):
    __tablename__ = "telemetry_readings"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(40), nullable=False, default="manual")  # wearable_webhook / iot_sensor / manual
    device_name = Column(String(120), nullable=True)
    heart_rate_bpm = Column(Float, nullable=True)
    speed_kmh = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=True)
    duration_minutes = Column(Float, nullable=True)
    calories = Column(Float, nullable=True)
    muscle_load_pct = Column(Float, nullable=True)
    fatigue_index = Column(Float, nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class VideoAnalysis(Base):
    __tablename__ = "video_analyses"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    original_filename = Column(String(255), nullable=False)
    stored_video_path = Column(String(500), nullable=False)
    sport = Column(String(80), nullable=True)
    exercise_type = Column(String(50), nullable=True)
    duration_seconds = Column(Float, nullable=False)
    fps = Column(Float, nullable=False)
    frame_count = Column(Integer, nullable=False)
    resolution = Column(String(30), nullable=False)
    mean_motion_intensity = Column(Float, nullable=False)
    peak_motion_intensity = Column(Float, nullable=False)
    active_movement_ratio_pct = Column(Float, nullable=False)
    motion_timeline = Column(JSON, nullable=False, default=list)
    trajectory_points = Column(JSON, nullable=False, default=list)
    key_moments = Column(JSON, nullable=False, default=list)
    feedback_items = Column(JSON, nullable=False, default=list)
    linked_prediction_id = Column(Integer, ForeignKey("ai_predictions.id", ondelete="SET NULL"), nullable=True)
    analysis_disclaimer = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class SkillAssessment(Base):
    __tablename__ = "skill_assessments"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assessed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    overall_score = Column(Float, nullable=False)  # 0-100 transparent formula
    consistency_score = Column(Float, nullable=False)
    aerobic_efficiency_score = Column(Float, nullable=False)
    energy_output_score = Column(Float, nullable=False)
    recovery_discipline_score = Column(Float, nullable=False)
    workload_capacity_score = Column(Float, nullable=False)
    dataset_peer_percentile = Column(Float, nullable=True)
    db_cohort_rank = Column(Integer, nullable=True)
    db_cohort_total = Column(Integer, nullable=True)
    criteria_breakdown = Column(JSON, nullable=False, default=dict)
    strengths = Column(JSON, nullable=False, default=list)
    improvement_areas = Column(JSON, nullable=False, default=list)
    sessions_analyzed = Column(Integer, nullable=False, default=0)
    predictions_analyzed = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(60), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(40), nullable=False, default="trophy")
    points = Column(Integer, nullable=False, default=50)
    category = Column(String(40), nullable=False, default="milestone")


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False)
    earned_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    metric_type = Column(String(50), nullable=False)  # calories / sessions / duration_minutes / distance_km
    target_value = Column(Float, nullable=False)
    reward_points = Column(Integer, nullable=False, default=100)
    reward_title = Column(String(120), nullable=True)
    start_date = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class ChallengeParticipation(Base):
    __tablename__ = "challenge_participations"
    __table_args__ = (UniqueConstraint("challenge_id", "user_id", name="uq_challenge_user"),)

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    current_value = Column(Float, nullable=False, default=0.0)
    is_completed = Column(Boolean, default=False, nullable=False)
    joined_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    athlete_context_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    sender = Column(String(20), nullable=False)  # user / assistant
    message = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(60), nullable=False)
    entity_id = Column(Integer, nullable=True)
    summary = Column(String(300), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
