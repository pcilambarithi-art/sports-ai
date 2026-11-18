"""
Domain coaching intelligence services strictly grounded in real database records,
real trained ML model outputs (when ready), and transparent sports-science formulas.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy.orm import Session

from app.db.models import (
    AIPrediction,
    Achievement,
    AthleteProfile,
    Challenge,
    ChallengeParticipation,
    GameStrategy,
    InjuryRiskAssessment,
    Opponent,
    PerformanceRecord,
    SkillAssessment,
    TelemetryReading,
    TrainingProgram,
    TrainingSession,
    User,
    UserAchievement,
    VideoAnalysis,
)
from app.ml.model_service import VALID_EXERCISE_TYPES, model_service

DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _safe_athlete_defaults(profile: Optional[AthleteProfile]) -> Dict[str, Any]:
    return {
        "Age": float(profile.age if profile and profile.age else 26),
        "Gender": profile.gender if profile and profile.gender else "Male",
        "Weight_KG": float(profile.weight_kg if profile and profile.weight_kg else 72.0),
        "Workout_Frequency_Per_Week": float(
            profile.workout_frequency_per_week if profile and profile.workout_frequency_per_week else 4
        ),
        "Sleep_Hours": float(profile.avg_sleep_hours if profile and profile.avg_sleep_hours else 7.2),
        "Water_Intake_Liters": float(
            profile.avg_water_intake_liters if profile and profile.avg_water_intake_liters else 2.5
        ),
        "Fitness_Goal": profile.fitness_goal if profile and profile.fitness_goal else "General Fitness",
        "Experience_Level": profile.experience_level if profile and profile.experience_level else "Intermediate",
    }


# =====================================================================
# 1. PERSONALIZED TRAINING PROGRAM GENERATION & ADAPTIVE ADJUSTMENT
# =====================================================================


def generate_training_program(
    db: Session,
    athlete: User,
    created_by: User,
    title: Optional[str] = None,
    sport: Optional[str] = None,
    goal: Optional[str] = None,
    experience_level: Optional[str] = None,
    weekly_sessions: Optional[int] = None,
) -> TrainingProgram:
    profile = db.query(AthleteProfile).filter(AthleteProfile.user_id == athlete.id).first()
    recent_records = (
        db.query(PerformanceRecord)
        .filter(PerformanceRecord.athlete_id == athlete.id)
        .order_by(PerformanceRecord.session_date.desc())
        .limit(12)
        .all()
    )

    resolved_goal = goal or (profile.fitness_goal if profile and profile.fitness_goal else "Endurance")
    resolved_exp = experience_level or (
        profile.experience_level if profile and profile.experience_level else "Intermediate"
    )
    resolved_sport = sport or (profile.sport if profile and profile.sport else "Multi-Sport Conditioning")
    resolved_freq = weekly_sessions or (
        profile.workout_frequency_per_week if profile and profile.workout_frequency_per_week else 4
    )
    resolved_freq = max(2, min(7, int(resolved_freq)))

    # Adapt duration/HR from actual logged athlete history if available
    if recent_records:
        avg_dur = float(np.mean([r.duration_minutes for r in recent_records]))
        avg_hr = float(np.mean([r.heart_rate_bpm for r in recent_records]))
        avg_rpe = [r.rpe_score for r in recent_records if r.rpe_score is not None]
        mean_rpe = float(np.mean(avg_rpe)) if avg_rpe else 6.5
        dur_scale = 0.9 if mean_rpe >= 8.2 else (1.08 if mean_rpe <= 5.5 else 1.0)
        base_duration = max(25.0, min(90.0, round(avg_dur * dur_scale, 0)))
        base_hr = max(115.0, min(172.0, round(avg_hr, 0)))
        adaptation_note = (
            f"Calibrated from {len(recent_records)} logged sessions "
            f"(avg {avg_dur:.0f} min @ {avg_hr:.0f} BPM, mean RPE {mean_rpe:.1f}/10)."
        )
    else:
        exp_dur_map = {"Beginner": 35.0, "Intermediate": 45.0, "Advanced": 60.0}
        exp_hr_map = {"Beginner": 132.0, "Intermediate": 146.0, "Advanced": 158.0}
        base_duration = exp_dur_map.get(resolved_exp, 45.0)
        base_hr = exp_hr_map.get(resolved_exp, 145.0)
        adaptation_note = (
            f"Initialized from {resolved_exp} profile baseline for {resolved_goal}. "
            "Log completed sessions to enable adaptive load calibration."
        )

    # Goal-specific exercise templates (all mapped to valid trained model Exercise_Type values)
    goal_templates: Dict[str, List[Dict[str, Any]]] = {
        "Weight Loss": [
            {"exercise": "HIIT", "focus": "Metabolic Interval Conditioning", "dur_mult": 0.75, "hr_delta": 14, "intensity": "High"},
            {"exercise": "Running", "focus": "Tempo Aerobic Fat Oxidation", "dur_mult": 1.05, "hr_delta": 4, "intensity": "Moderate"},
            {"exercise": "Weight Training", "focus": "Full-Body Lean Mass Retention", "dur_mult": 0.95, "hr_delta": -8, "intensity": "Moderate"},
            {"exercise": "Cycling", "focus": "Zone 2 Sustained Output", "dur_mult": 1.15, "hr_delta": -6, "intensity": "Moderate"},
            {"exercise": "Rowing", "focus": "Power-Endurance Ergometer", "dur_mult": 0.85, "hr_delta": 8, "intensity": "High"},
            {"exercise": "Walking", "focus": "Active Recovery Brisk Stride", "dur_mult": 1.0, "hr_delta": -25, "intensity": "Recovery"},
            {"exercise": "Yoga", "focus": "Mobility & Parasympathetic Recovery", "dur_mult": 0.8, "hr_delta": -32, "intensity": "Recovery"},
        ],
        "Endurance": [
            {"exercise": "Running", "focus": "Aerobic Base Progression", "dur_mult": 1.1, "hr_delta": 0, "intensity": "Moderate"},
            {"exercise": "Cycling", "focus": "Cadence & Threshold Endurance", "dur_mult": 1.2, "hr_delta": 4, "intensity": "Moderate"},
            {"exercise": "Swimming", "focus": "Low-Impact Cardiorespiratory Volume", "dur_mult": 1.0, "hr_delta": -4, "intensity": "Moderate"},
            {"exercise": "Rowing", "focus": "Lactate Threshold Intervals", "dur_mult": 0.9, "hr_delta": 10, "intensity": "High"},
            {"exercise": "Weight Training", "focus": "Posterior Chain & Core Durability", "dur_mult": 0.85, "hr_delta": -10, "intensity": "Moderate"},
            {"exercise": "Running", "focus": "Long Steady Distance", "dur_mult": 1.25, "hr_delta": -4, "intensity": "Moderate"},
            {"exercise": "Yoga", "focus": "Hip/Ankle Mobility & Recovery", "dur_mult": 0.75, "hr_delta": -32, "intensity": "Recovery"},
        ],
        "Muscle Gain": [
            {"exercise": "Weight Training", "focus": "Upper Body Hypertrophy & Strength", "dur_mult": 1.1, "hr_delta": -8, "intensity": "High"},
            {"exercise": "Weight Training", "focus": "Lower Body Compound Power", "dur_mult": 1.15, "hr_delta": -4, "intensity": "High"},
            {"exercise": "Rowing", "focus": "Anaerobic Power Conditioning", "dur_mult": 0.75, "hr_delta": 8, "intensity": "Moderate"},
            {"exercise": "Weight Training", "focus": "Push/Pull Hypertrophy Volume", "dur_mult": 1.1, "hr_delta": -6, "intensity": "High"},
            {"exercise": "HIIT", "focus": "Short Sprint Work Capacity", "dur_mult": 0.65, "hr_delta": 12, "intensity": "High"},
            {"exercise": "Walking", "focus": "Recovery Flush & Joint Care", "dur_mult": 0.9, "hr_delta": -26, "intensity": "Recovery"},
            {"exercise": "Yoga", "focus": "Fascial Release & Flexibility", "dur_mult": 0.8, "hr_delta": -32, "intensity": "Recovery"},
        ],
        "Flexibility": [
            {"exercise": "Yoga", "focus": "Dynamic Mobility & Flow", "dur_mult": 1.0, "hr_delta": -28, "intensity": "Low"},
            {"exercise": "Swimming", "focus": "Full Range-of-Motion Conditioning", "dur_mult": 0.95, "hr_delta": -6, "intensity": "Moderate"},
            {"exercise": "Yoga", "focus": "Deep Joint Stability & Balance", "dur_mult": 1.05, "hr_delta": -30, "intensity": "Low"},
            {"exercise": "Walking", "focus": "Postural Aerobic Stride", "dur_mult": 1.0, "hr_delta": -22, "intensity": "Low"},
            {"exercise": "Weight Training", "focus": "End-Range Eccentric Strength", "dur_mult": 0.85, "hr_delta": -10, "intensity": "Moderate"},
            {"exercise": "Cycling", "focus": "Low-Impact Aerobic Flush", "dur_mult": 0.9, "hr_delta": -8, "intensity": "Moderate"},
            {"exercise": "Yoga", "focus": "Restorative Recovery Flow", "dur_mult": 0.9, "hr_delta": -34, "intensity": "Recovery"},
        ],
    }
    templates = goal_templates.get(resolved_goal, goal_templates["Endurance"])

    # Pick active training days evenly distributed across the week
    active_day_indices = sorted(
        set(int(round(i * 6 / max(resolved_freq - 1, 1))) for i in range(resolved_freq))
    )
    if len(active_day_indices) < resolved_freq:
        for d in range(7):
            if d not in active_day_indices:
                active_day_indices.append(d)
            if len(active_day_indices) == resolved_freq:
                break
        active_day_indices.sort()

    defaults = _safe_athlete_defaults(profile)
    defaults["Fitness_Goal"] = resolved_goal
    defaults["Experience_Level"] = resolved_exp
    defaults["Workout_Frequency_Per_Week"] = float(resolved_freq)

    program = TrainingProgram(
        athlete_id=athlete.id,
        created_by_id=created_by.id,
        title=title or f"{resolved_sport} — {resolved_goal} ({resolved_exp})",
        sport=resolved_sport,
        goal=resolved_goal,
        experience_level=resolved_exp,
        weekly_target_sessions=resolved_freq,
        status="active",
        adaptation_notes=adaptation_note,
        generated_by_ai=True,
    )
    db.add(program)
    db.flush()

    session_rows_for_ml: List[Dict[str, Any]] = []
    created_sessions: List[TrainingSession] = []

    active_counter = 0
    for day_idx in range(7):
        day_name = DAYS_OF_WEEK[day_idx]
        if day_idx in active_day_indices:
            tpl = templates[active_counter % len(templates)]
            active_counter += 1
            dur = float(max(15.0, min(120.0, round(base_duration * tpl["dur_mult"]))))
            hr = float(max(95.0, min(178.0, round(base_hr + tpl["hr_delta"]))))
            sess = TrainingSession(
                program_id=program.id,
                day_of_week=day_name,
                day_index=day_idx + 1,
                exercise_type=tpl["exercise"],
                focus_area=tpl["focus"],
                target_duration_minutes=dur,
                target_heart_rate_bpm=hr,
                intensity=tpl["intensity"],
                instructions=(
                    f"10 min dynamic warm-up -> {int(dur)} min {tpl['exercise']} focusing on "
                    f"{tpl['focus']} (target HR ~{int(hr)} BPM) -> 5 min cooldown & hydration."
                ),
            )
            db.add(sess)
            created_sessions.append(sess)
            row = dict(defaults)
            row["Exercise_Type"] = tpl["exercise"]
            row["Duration_Minutes"] = dur
            row["Heart_Rate_BPM"] = hr
            session_rows_for_ml.append(row)
        else:
            sess = TrainingSession(
                program_id=program.id,
                day_of_week=day_name,
                day_index=day_idx + 1,
                exercise_type="Yoga",
                focus_area="Scheduled Rest & Light Mobility",
                target_duration_minutes=20.0,
                target_heart_rate_bpm=98.0,
                intensity="Recovery",
                instructions="Rest day: prioritize 7.5+ hours sleep, hydration, and optional 20 min mobility stretching.",
            )
            db.add(sess)
            created_sessions.append(sess)
            row = dict(defaults)
            row["Exercise_Type"] = "Yoga"
            row["Duration_Minutes"] = 20.0
            row["Heart_Rate_BPM"] = 98.0
            session_rows_for_ml.append(row)

    # Populate real expected calories using the user's trained model when ready
    if model_service.status == "ready" and session_rows_for_ml:
        try:
            preds = model_service.predict_batch_fast(session_rows_for_ml)
            total_cals = 0.0
            for sess, cal in zip(created_sessions, preds):
                sess.expected_calories = cal
                if sess.intensity != "Recovery":
                    total_cals += cal
            program.weekly_target_calories = round(total_cals, 1)
        except Exception:
            program.weekly_target_calories = None

    db.commit()
    db.refresh(program)
    return program


def adapt_training_program(db: Session, program: TrainingProgram) -> TrainingProgram:
    """Adapt remaining uncompleted sessions based on real feedback RPE and completion progress."""
    sessions = (
        db.query(TrainingSession)
        .filter(TrainingSession.program_id == program.id)
        .order_by(TrainingSession.day_index.asc())
        .all()
    )
    completed = [s for s in sessions if s.is_completed]
    rpes = [s.feedback_rpe for s in completed if s.feedback_rpe is not None]

    if not completed:
        program.adaptation_notes = (
            "No completed sessions yet. Complete at least one session with RPE feedback to adapt load."
        )
        db.commit()
        db.refresh(program)
        return program

    mean_rpe = float(np.mean(rpes)) if rpes else 6.5
    if mean_rpe >= 8.0:
        dur_factor, hr_delta = 0.88, -6.0
        reason = f"High reported effort (avg RPE {mean_rpe:.1f}/10 across {len(completed)} sessions): reduced remaining volume by 12% and lowered target HR by 6 BPM to prevent overreaching."
    elif mean_rpe <= 5.0:
        dur_factor, hr_delta = 1.12, 5.0
        reason = f"Low reported effort (avg RPE {mean_rpe:.1f}/10 across {len(completed)} sessions): progressed remaining volume by 12% and increased target HR by 5 BPM for progressive overload."
    else:
        dur_factor, hr_delta = 1.03, 2.0
        reason = f"Optimal training strain (avg RPE {mean_rpe:.1f}/10 across {len(completed)} sessions): applied gentle +3% progression on remaining sessions."

    profile = db.query(AthleteProfile).filter(AthleteProfile.user_id == program.athlete_id).first()
    defaults = _safe_athlete_defaults(profile)
    defaults["Fitness_Goal"] = program.goal
    defaults["Experience_Level"] = program.experience_level
    defaults["Workout_Frequency_Per_Week"] = float(program.weekly_target_sessions)

    pending = [s for s in sessions if not s.is_completed and s.intensity != "Recovery"]
    ml_rows = []
    for s in pending:
        s.target_duration_minutes = float(max(15.0, min(120.0, round(s.target_duration_minutes * dur_factor))))
        s.target_heart_rate_bpm = float(max(95.0, min(178.0, round(s.target_heart_rate_bpm + hr_delta))))
        row = dict(defaults)
        row["Exercise_Type"] = s.exercise_type
        row["Duration_Minutes"] = s.target_duration_minutes
        row["Heart_Rate_BPM"] = s.target_heart_rate_bpm
        ml_rows.append(row)

    if model_service.status == "ready" and ml_rows:
        try:
            preds = model_service.predict_batch_fast(ml_rows)
            for s, cal in zip(pending, preds):
                s.expected_calories = cal
            program.weekly_target_calories = round(
                sum((s.expected_calories or 0.0) for s in sessions if s.intensity != "Recovery"), 1
            )
        except Exception:
            pass

    program.adaptation_notes = reason
    db.commit()
    db.refresh(program)
    return program


# =====================================================================
# 2. INJURY RISK ASSESSMENT & ANOMALY DETECTION (NON-MEDICAL WORKLOAD)
# =====================================================================


def assess_injury_risk(
    db: Session,
    athlete: User,
    assessed_by: User,
) -> InjuryRiskAssessment:
    now = datetime.now(timezone.utc)
    cutoff_28d = now - timedelta(days=28)
    cutoff_7d = now - timedelta(days=7)

    records = (
        db.query(PerformanceRecord)
        .filter(PerformanceRecord.athlete_id == athlete.id, PerformanceRecord.session_date >= cutoff_28d)
        .order_by(PerformanceRecord.session_date.asc())
        .all()
    )
    profile = db.query(AthleteProfile).filter(AthleteProfile.user_id == athlete.id).first()

    # Session load proxy = duration_minutes * (rpe_score or heart_rate_bpm / 20)
    def _session_load(r: PerformanceRecord) -> float:
        intensity_factor = float(r.rpe_score) if r.rpe_score else (float(r.heart_rate_bpm) / 20.0)
        return float(r.duration_minutes) * intensity_factor

    def _as_utc(dt: datetime) -> datetime:
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)

    recent_7d = [r for r in records if _as_utc(r.session_date) >= cutoff_7d]
    acute_load = round(sum(_session_load(r) for r in recent_7d), 1)
    chronic_total = sum(_session_load(r) for r in records)
    chronic_weekly_avg = round(chronic_total / 4.0, 1) if records else 0.0
    acwr = round(acute_load / chronic_weekly_avg, 2) if chronic_weekly_avg > 0 else None

    risk_score = 10.0  # baseline monitoring score
    risk_factors: List[str] = []
    anomalies: List[str] = []
    preventive: List[str] = []
    modifications: List[str] = []

    if not records:
        risk_factors.append(
            "No performance sessions logged in the last 28 days. Risk score reflects baseline profile indicators only."
        )
    else:
        if acwr is not None:
            if acwr >= 1.5:
                risk_score += 38.0
                risk_factors.append(
                    f"Elevated Acute:Chronic Workload Ratio (ACWR = {acwr}, above 1.50 spike threshold)."
                )
                anomalies.append(f"7-day workload spike detected ({acute_load:.0f} AU vs 28-day weekly avg {chronic_weekly_avg:.0f} AU).")
                modifications.append("Reduce total session duration by 20-30% over the next 5 days to normalize ACWR.")
            elif acwr >= 1.3:
                risk_score += 20.0
                risk_factors.append(f"Moderate workload ramp (ACWR = {acwr}, approaching 1.50 caution band).")
                modifications.append("Avoid stacking consecutive high-intensity sessions this week.")

        # Heart rate load check
        hrs = [float(r.heart_rate_bpm) for r in recent_7d]
        if hrs and max(hrs) >= 172:
            risk_score += 14.0
            risk_factors.append(f"Sustained peak heart rate exposure detected ({max(hrs):.0f} BPM in last 7 days).")
            modifications.append("Substitute one high-HR workout with Zone 2 aerobic recovery (120-138 BPM).")

        # Fatigue & RPE check
        fatigues = [r.fatigue_level for r in recent_7d if r.fatigue_level is not None]
        if fatigues and float(np.mean(fatigues)) >= 7.5:
            risk_score += 18.0
            risk_factors.append(f"High reported fatigue (7-day mean {np.mean(fatigues):.1f}/10).")
            anomalies.append("Persistent elevated athlete fatigue score.")
            modifications.append("Insert an active recovery or full rest day before resuming intense drills.")

        # Z-score anomaly detection on session duration or heart rate across 28d history
        if len(records) >= 4:
            all_durs = np.array([r.duration_minutes for r in records], dtype=float)
            dur_std = float(all_durs.std())
            if dur_std > 0:
                latest_z = (all_durs[-1] - float(all_durs.mean())) / dur_std
                if latest_z >= 1.8:
                    risk_score += 12.0
                    anomalies.append(
                        f"Session duration anomaly: latest session ({all_durs[-1]:.0f} min) is +{latest_z:.1f} SD above personal 28-day mean ({all_durs.mean():.0f} min)."
                    )

        # Sleep & Hydration recovery indicators
        sleeps = [r.sleep_hours for r in recent_7d if r.sleep_hours is not None]
        if not sleeps and profile and profile.avg_sleep_hours:
            sleeps = [profile.avg_sleep_hours]
        if sleeps and float(np.mean(sleeps)) < 6.5:
            risk_score += 14.0
            risk_factors.append(f"Recovery sleep deficit detected (avg {np.mean(sleeps):.1f} hrs/night, target >= 7.0 hrs).")
            modifications.append("Prioritize 7.5-8.5 hours sleep and defer maximal sprint/HIIT sessions until rested.")

        waters = [r.water_intake_liters for r in recent_7d if r.water_intake_liters is not None]
        if not waters and profile and profile.avg_water_intake_liters:
            waters = [profile.avg_water_intake_liters]
        if waters and float(np.mean(waters)) < 2.0:
            risk_score += 8.0
            risk_factors.append(f"Low hydration intake ({np.mean(waters):.1f} L/day, recommended >= 2.5 L for active athletes).")

    risk_score = round(min(100.0, max(5.0, risk_score)), 1)
    if risk_score >= 65.0:
        risk_level = "High"
        coach_alert = True
    elif risk_score >= 38.0:
        risk_level = "Moderate"
        coach_alert = len(anomalies) > 0
    else:
        risk_level = "Low"
        coach_alert = False

    preventive.extend(
        [
            "10-minute dynamic warm-up with hip/ankle mobility and progressive activation before main sets.",
            "Eccentric lower-limb durability (Nordic hamstring lowers & calf eccentrics, 2x8 twice weekly).",
            "Core anti-rotation stability (Pallof press & dead-bugs) to maintain biomechanics under fatigue.",
        ]
    )
    if risk_level == "High":
        preventive.append("Schedule 20 min guided parasympathetic cooldown / mobility flow and coach load review.")
    if not modifications:
        modifications.append("Current workload indicators are within sustainable range. Maintain progressive 5-10% weekly load cap.")

    assessment = InjuryRiskAssessment(
        athlete_id=athlete.id,
        assessed_by_id=assessed_by.id,
        risk_score=risk_score,
        risk_level=risk_level,
        acute_load_7d=acute_load,
        chronic_load_28d=chronic_weekly_avg,
        acwr=acwr,
        anomalies_detected=anomalies,
        risk_factors=risk_factors,
        preventive_exercises=preventive,
        training_modifications=modifications,
        coach_alert_required=coach_alert,
        coach_acknowledged=False,
        disclaimer=(
            "Workload-based injury risk indicator computed from logged training duration, heart rate, "
            "RPE, fatigue, sleep, and hydration rules (not produced by the calorie ML model and NOT a medical diagnosis). "
            "Consult a qualified sports physician or physiotherapist for pain or clinical injury evaluation."
        ),
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


# =====================================================================
# 3. GAME STRATEGY OPTIMIZATION & SCENARIO SIMULATION
# =====================================================================


def generate_game_strategy(
    db: Session,
    opponent: Opponent,
    created_by: User,
    athlete: Optional[User] = None,
    title: Optional[str] = None,
    tempo_adjustment_pct: float = 0.0,
    defensive_focus_pct: float = 50.0,
) -> GameStrategy:
    # Gather actual logged metrics for the selected athlete (or team-wide if none specified)
    rec_q = db.query(PerformanceRecord)
    if athlete:
        rec_q = rec_q.filter(PerformanceRecord.athlete_id == athlete.id)
    records = rec_q.order_by(PerformanceRecord.session_date.desc()).limit(30).all()

    our_speeds = [r.speed_kmh for r in records if r.speed_kmh is not None]
    our_durs = [r.duration_minutes for r in records]
    our_avg_speed = round(float(np.mean(our_speeds)), 2) if our_speeds else None
    our_avg_endurance = round(float(np.mean(our_durs)), 1) if our_durs else None

    availability_notes: List[str] = []
    comparison: Dict[str, Any] = {
        "speed_kmh": {
            "ours": our_avg_speed,
            "opponent": opponent.avg_speed_kmh,
            "available": our_avg_speed is not None and opponent.avg_speed_kmh is not None,
        },
        "endurance_minutes": {
            "ours": our_avg_endurance,
            "opponent": opponent.endurance_minutes,
            "available": our_avg_endurance is not None and opponent.endurance_minutes is not None,
        },
        "opponent_win_rate_pct": opponent.win_rate_pct,
        "opponent_offensive_rating": opponent.offensive_rating,
        "opponent_defensive_rating": opponent.defensive_rating,
    }

    counters: List[str] = []
    if opponent.avg_speed_kmh is None:
        availability_notes.append("Opponent average speed data is unavailable.")
    elif our_avg_speed is None:
        availability_notes.append("No athlete speed logs recorded yet to compare against opponent speed.")
    else:
        if our_avg_speed >= opponent.avg_speed_kmh:
            counters.append(
                f"Speed Advantage ({our_avg_speed} vs {opponent.avg_speed_kmh} km/h): Push fast transitions and stretch the field/pace early."
            )
        else:
            counters.append(
                f"Speed Deficit ({our_avg_speed} vs {opponent.avg_speed_kmh} km/h): Compact spatial spacing, deny open-lane sprints, and control tempo."
            )

    if opponent.endurance_minutes is None:
        availability_notes.append("Opponent endurance duration data is unavailable.")
    elif our_avg_endurance is None:
        availability_notes.append("No athlete duration logs recorded yet to compare against opponent endurance.")
    else:
        if our_avg_endurance >= opponent.endurance_minutes:
            counters.append(
                f"Endurance Edge ({our_avg_endurance} vs {opponent.endurance_minutes} min): Maintain sustained pressure in late periods/quarters when opponent output drops."
            )
        else:
            counters.append(
                f"Endurance Gap ({our_avg_endurance} vs {opponent.endurance_minutes} min): Use strategic substitutions/pacing blocks and conserve anaerobic bursts for decisive moments."
            )

    if opponent.offensive_rating is not None and opponent.defensive_rating is not None:
        if opponent.offensive_rating > opponent.defensive_rating + 8:
            counters.append(
                f"Opponent is offense-heavy (Off {opponent.offensive_rating:.0f} vs Def {opponent.defensive_rating:.0f}): Absorb initial surges and counterattack exposed transition lanes."
            )
        elif opponent.defensive_rating > opponent.offensive_rating + 8:
            counters.append(
                f"Opponent is defense-first (Def {opponent.defensive_rating:.0f} vs Off {opponent.offensive_rating:.0f}): Use width, quick ball/pace reversals, and set-piece precision to unlock low blocks."
            )
    else:
        availability_notes.append("Opponent offensive/defensive ratings are incomplete — enter verified scouting ratings for deeper matchup scoring.")

    if opponent.observed_weaknesses:
        counters.append(f"Exploit Scouted Weakness: Target '{opponent.observed_weaknesses.strip()}' systematically during key intervals.")
    if opponent.observed_strengths:
        counters.append(f"Neutralize Scouted Strength: Assign dedicated containment against '{opponent.observed_strengths.strip()}'.")
    if not counters:
        counters.append("Add verified opponent metrics or scouting notes to generate specific metric-backed counter-strategies.")

    # Deterministic scenario projections (explicitly labeled as tactical simulation projections)
    base_off = opponent.offensive_rating if opponent.offensive_rating is not None else 50.0
    base_def = opponent.defensive_rating if opponent.defensive_rating is not None else 50.0
    scenarios = [
        {
            "scenario_name": "High-Tempo Pressing (+15% Pace)",
            "tempo_shift_pct": 15,
            "defensive_balance_pct": 35,
            "projected_control_index": round(min(95, max(20, 55 + (100 - base_def) * 0.25 - base_off * 0.12)), 1),
            "fatigue_cost": "High",
            "tactical_note": "Best used if your endurance capacity exceeds opponent's; increases late-game fatigue load.",
        },
        {
            "scenario_name": "Balanced Adaptive Tempo (Configured)",
            "tempo_shift_pct": tempo_adjustment_pct,
            "defensive_balance_pct": defensive_focus_pct,
            "projected_control_index": round(
                min(95, max(20, 52 + (defensive_focus_pct - 50) * 0.18 + tempo_adjustment_pct * 0.25 + (base_def - base_off) * -0.05)),
                1,
            ),
            "fatigue_cost": "Moderate",
            "tactical_note": "Matches your custom tempo/defensive slider parameters for steady energy management.",
        },
        {
            "scenario_name": "Compact Counter-Attack (-10% Pace, 70% Def)",
            "tempo_shift_pct": -10,
            "defensive_balance_pct": 70,
            "projected_control_index": round(min(95, max(20, 54 + (100 - base_off) * 0.22)), 1),
            "fatigue_cost": "Low-Moderate",
            "tactical_note": "Reduces exposure against faster or higher-scoring opponents while preserving late sprint energy.",
        },
    ]

    summary = (
        f"Tactical game plan against {opponent.name} ({opponent.sport}). "
        f"Evaluated using {len(records)} actual logged performance sessions and verified scouting inputs. "
        "Scenario projections are deterministic tactical models—not guaranteed match outcomes."
    )

    strategy = GameStrategy(
        opponent_id=opponent.id,
        athlete_id=athlete.id if athlete else None,
        created_by_id=created_by.id,
        title=title or f"Matchup Plan vs {opponent.name}",
        tactical_summary=summary,
        counter_strategies=counters,
        comparison_metrics=comparison,
        scenario_simulations=scenarios,
        data_availability_notes=availability_notes,
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy


# =====================================================================
# 4. SKILL ASSESSMENT, PREDICTIVE ANALYTICS & PEAK WINDOW FORECAST
# =====================================================================


def evaluate_skill_assessment(
    db: Session,
    athlete: User,
    assessed_by: User,
) -> SkillAssessment:
    records = (
        db.query(PerformanceRecord)
        .filter(PerformanceRecord.athlete_id == athlete.id)
        .order_by(PerformanceRecord.session_date.asc())
        .all()
    )
    predictions = (
        db.query(AIPrediction)
        .filter(AIPrediction.athlete_id == athlete.id)
        .order_by(AIPrediction.created_at.asc())
        .all()
    )
    profile = db.query(AthleteProfile).filter(AthleteProfile.user_id == athlete.id).first()

    if not records and not predictions:
        raise ValueError(
            "Cannot compute a real skill assessment yet: no logged training sessions or AI predictions exist for this athlete."
        )

    # 1. Consistency Score (25%): sessions in last 14 days vs weekly target * 2
    now = datetime.now(timezone.utc)
    cutoff_14d = now - timedelta(days=14)
    def _as_utc(dt: datetime) -> datetime:
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)

    recent_14d = [r for r in records if _as_utc(r.session_date) >= cutoff_14d]
    target_wk = profile.workout_frequency_per_week if profile and profile.workout_frequency_per_week else 4
    consistency = min(100.0, round((len(recent_14d) / max(target_wk * 2.0, 1.0)) * 100.0, 1)) if records else 0.0

    # 2. Energy Output Score (25%): mean dataset percentile from real trained ML predictions or calories
    percentiles = [p.dataset_percentile for p in predictions if p.dataset_percentile is not None]
    if percentiles:
        energy_output = round(float(np.mean(percentiles)), 1)
        dataset_pct = energy_output
    else:
        cals = [r.calories_burned or r.ai_predicted_calories for r in records if (r.calories_burned or r.ai_predicted_calories)]
        if cals:
            # Compare against 70k dataset mean (477.5 kcal)
            ds_mean = model_service.dataset_stats.get("target_summary", {}).get("mean", 477.5)
            energy_output = min(100.0, round((float(np.mean(cals)) / max(ds_mean * 1.4, 1.0)) * 100.0, 1))
            dataset_pct = model_service._compute_dataset_percentile(float(np.mean(cals)), records[-1].exercise_type)
        else:
            energy_output = 0.0
            dataset_pct = None

    # 3. Aerobic Efficiency Score (20%): calories burned per minute per 100 BPM (measurable burn efficiency)
    eff_vals = []
    for p in predictions:
        if p.heart_rate_bpm > 0:
            eff_vals.append((p.burn_rate_per_min / (p.heart_rate_bpm / 100.0)))
    for r in records:
        cal = r.calories_burned or r.ai_predicted_calories
        if cal and r.duration_minutes > 0 and r.heart_rate_bpm > 0:
            eff_vals.append(((cal / r.duration_minutes) / (r.heart_rate_bpm / 100.0)))
    # Typical efficient burn rate per 100 BPM is ~4.5 to 9.5
    aerobic_eff = min(100.0, max(0.0, round((float(np.mean(eff_vals)) / 8.5) * 100.0, 1))) if eff_vals else 0.0

    # 4. Workload Capacity Score (15%): average session duration relative to 75 min benchmark
    durs = [r.duration_minutes for r in records] or [p.duration_minutes for p in predictions]
    workload_cap = min(100.0, round((float(np.mean(durs)) / 75.0) * 100.0, 1)) if durs else 0.0

    # 5. Recovery Discipline Score (15%): sleep (target 7.5h) + hydration (target 2.8L)
    sleeps = [r.sleep_hours for r in records if r.sleep_hours is not None] or [p.sleep_hours for p in predictions]
    waters = [r.water_intake_liters for r in records if r.water_intake_liters is not None] or [p.water_intake_liters for p in predictions]
    sleep_sub = min(100.0, (float(np.mean(sleeps)) / 7.5) * 100.0) if sleeps else 50.0
    water_sub = min(100.0, (float(np.mean(waters)) / 2.8) * 100.0) if waters else 50.0
    recovery_disc = round((sleep_sub * 0.6) + (water_sub * 0.4), 1)

    overall = round(
        consistency * 0.25
        + energy_output * 0.25
        + aerobic_eff * 0.20
        + workload_cap * 0.15
        + recovery_disc * 0.15,
        1,
    )

    # Real peer cohort ranking across athletes in DB who have assessments
    existing_latest: Dict[int, float] = {}
    all_assessments = db.query(SkillAssessment).order_by(SkillAssessment.created_at.asc()).all()
    for a in all_assessments:
        existing_latest[a.athlete_id] = a.overall_score
    existing_latest[athlete.id] = overall
    sorted_scores = sorted(existing_latest.values(), reverse=True)
    cohort_rank = sorted_scores.index(overall) + 1
    cohort_total = len(sorted_scores)

    dims = {
        "Training Consistency (25%)": consistency,
        "Energy Expenditure Output (25%)": energy_output,
        "Aerobic Burn Efficiency (20%)": aerobic_eff,
        "Workload Capacity (15%)": workload_cap,
        "Recovery Discipline (15%)": recovery_disc,
    }
    sorted_dims = sorted(dims.items(), key=lambda kv: kv[1], reverse=True)
    strengths = [f"{k}: {v}/100" for k, v in sorted_dims[:2]]
    improvements = [f"{k}: {v}/100" for k, v in sorted_dims[-2:]]

    criteria_breakdown = {
        "formula": "0.25*Consistency + 0.25*EnergyOutput + 0.20*AerobicEfficiency + 0.15*WorkloadCapacity + 0.15*RecoveryDiscipline",
        "benchmark_basis": (
            "Peer percentile computed directly from the 70,000-row workout training dataset and real athletes in your database. "
            "No invented professional benchmarks are used."
        ),
        "weights": {
            "consistency": 0.25,
            "energy_output": 0.25,
            "aerobic_efficiency": 0.20,
            "workload_capacity": 0.15,
            "recovery_discipline": 0.15,
        },
    }

    assessment = SkillAssessment(
        athlete_id=athlete.id,
        assessed_by_id=assessed_by.id,
        overall_score=overall,
        consistency_score=consistency,
        aerobic_efficiency_score=aerobic_eff,
        energy_output_score=energy_output,
        recovery_discipline_score=recovery_disc,
        workload_capacity_score=workload_cap,
        dataset_peer_percentile=dataset_pct,
        db_cohort_rank=cohort_rank,
        db_cohort_total=cohort_total,
        criteria_breakdown=criteria_breakdown,
        strengths=strengths,
        improvement_areas=improvements,
        sessions_analyzed=len(records),
        predictions_analyzed=len(predictions),
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def compute_predictive_analytics(db: Session, athlete_id: int) -> Dict[str, Any]:
    """Forecast improvement trend & peak competition window strictly from logged history."""
    records = (
        db.query(PerformanceRecord)
        .filter(PerformanceRecord.athlete_id == athlete_id)
        .order_by(PerformanceRecord.session_date.asc())
        .all()
    )
    if len(records) < 3:
        return {
            "available": False,
            "sessions_count": len(records),
            "message": f"At least 3 logged training sessions are required to forecast performance trends (currently {len(records)}).",
            "forecast_points": [],
            "peak_window": None,
        }

    # Burn rate progression across chronological sessions
    y_vals = []
    labels = []
    for i, r in enumerate(records):
        cal = r.calories_burned or r.ai_predicted_calories or 0.0
        rate = (cal / r.duration_minutes) if (cal > 0 and r.duration_minutes > 0) else (r.duration_minutes / 10.0)
        y_vals.append(round(float(rate), 2))
        labels.append(r.session_date.strftime("%Y-%m-%d"))

    x = np.arange(len(y_vals), dtype=float)
    y = np.array(y_vals, dtype=float)
    slope, intercept = np.polyfit(x, y, 1)

    forecast_points = [
        {"step": f"Session {i+1}", "date": labels[i], "actual": y_vals[i], "projected": round(float(intercept + slope * i), 2)}
        for i in range(len(y_vals))
    ]
    for fut in range(1, 5):
        idx = len(y_vals) - 1 + fut
        forecast_points.append(
            {
                "step": f"Forecast +{fut}",
                "date": (datetime.now(timezone.utc) + timedelta(days=fut * 3)).strftime("%Y-%m-%d"),
                "actual": None,
                "projected": round(max(1.0, float(intercept + slope * idx)), 2),
            }
        )

    latest_risk = (
        db.query(InjuryRiskAssessment)
        .filter(InjuryRiskAssessment.athlete_id == athlete_id)
        .order_by(InjuryRiskAssessment.created_at.desc())
        .first()
    )
    taper_days = 10 if (latest_risk and latest_risk.risk_level == "High") else (7 if slope > 0 else 14)
    peak_start = (datetime.now(timezone.utc) + timedelta(days=taper_days)).strftime("%Y-%m-%d")
    peak_end = (datetime.now(timezone.utc) + timedelta(days=taper_days + 5)).strftime("%Y-%m-%d")

    return {
        "available": True,
        "sessions_count": len(records),
        "metric": "Session Output Rate (kcal/min)",
        "trend_slope_per_session": round(float(slope), 3),
        "trend_direction": "improving" if slope > 0.05 else ("declining" if slope < -0.05 else "stable"),
        "forecast_points": forecast_points,
        "peak_window": {
            "recommended_start": peak_start,
            "recommended_end": peak_end,
            "rationale": (
                f"Estimated {taper_days}-day taper window based on {len(records)} logged sessions "
                f"(slope {slope:+.2f}/session"
                + (f", latest workload risk: {latest_risk.risk_level}" if latest_risk else "")
                + ")."
            ),
        },
    }


# =====================================================================
# 5. GAMIFICATION EVALUATION & LEADERBOARD
# =====================================================================


def evaluate_user_achievements(db: Session, user_id: int) -> List[str]:
    """Check real DB activity and unlock earned badges."""
    pred_count = db.query(AIPrediction).filter(
        (AIPrediction.athlete_id == user_id) | (AIPrediction.requested_by_id == user_id)
    ).count()
    records = db.query(PerformanceRecord).filter(PerformanceRecord.athlete_id == user_id).all()
    session_count = len(records)
    total_cals = sum((r.calories_burned or r.ai_predicted_calories or 0.0) for r in records)
    video_count = db.query(VideoAnalysis).filter(
        (VideoAnalysis.athlete_id == user_id) | (VideoAnalysis.uploaded_by_id == user_id)
    ).count()
    completed_plan_sessions = (
        db.query(TrainingSession)
        .join(TrainingProgram, TrainingSession.program_id == TrainingProgram.id)
        .filter(TrainingProgram.athlete_id == user_id, TrainingSession.is_completed == True)  # noqa: E712
        .count()
    )
    completed_challenges = (
        db.query(ChallengeParticipation)
        .filter(ChallengeParticipation.user_id == user_id, ChallengeParticipation.is_completed == True)  # noqa: E712
        .count()
    )

    conditions = {
        "FIRST_PREDICTION": pred_count >= 1,
        "FIVE_PREDICTIONS": pred_count >= 5,
        "FIRST_SESSION": session_count >= 1,
        "CONSISTENCY_3": session_count >= 3,
        "ENDURANCE_1000": total_cals >= 1000.0,
        "VIDEO_BREAKDOWN": video_count >= 1,
        "PLAN_COMPLETED": completed_plan_sessions >= 3,
        "CHALLENGE_FINISHER": completed_challenges >= 1,
    }

    newly_unlocked: List[str] = []
    all_badges = {a.code: a for a in db.query(Achievement).all()}
    owned_ids = {
        ua.achievement_id
        for ua in db.query(UserAchievement).filter(UserAchievement.user_id == user_id).all()
    }

    for code, met in conditions.items():
        badge = all_badges.get(code)
        if met and badge and badge.id not in owned_ids:
            db.add(UserAchievement(user_id=user_id, achievement_id=badge.id))
            newly_unlocked.append(badge.name)

    if newly_unlocked:
        db.commit()
    return newly_unlocked


def build_leaderboard(db: Session) -> List[Dict[str, Any]]:
    users = db.query(User).filter(User.is_active == True).all()  # noqa: E712
    board = []
    for u in users:
        badge_points = (
            db.query(Achievement.points)
            .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
            .filter(UserAchievement.user_id == u.id)
            .all()
        )
        badge_xp = sum(p[0] for p in badge_points)
        records = db.query(PerformanceRecord).filter(PerformanceRecord.athlete_id == u.id).all()
        session_xp = len(records) * 25
        challenge_pts = (
            db.query(Challenge.reward_points)
            .join(ChallengeParticipation, ChallengeParticipation.challenge_id == Challenge.id)
            .filter(
                ChallengeParticipation.user_id == u.id,
                ChallengeParticipation.is_completed == True,  # noqa: E712
            )
            .all()
        )
        challenge_xp = sum(p[0] for p in challenge_pts)
        total_xp = badge_xp + session_xp + challenge_xp

        # Consistency streak = distinct training dates in last 14 days
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)
        def _as_utc(dt: datetime) -> datetime:
            return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)

        active_days_14d = len(
            {_as_utc(r.session_date).date() for r in records if _as_utc(r.session_date) >= cutoff}
        )
        board.append(
            {
                "user_id": u.id,
                "full_name": u.full_name,
                "role": u.role.value if hasattr(u.role, "value") else str(u.role),
                "total_points": total_xp,
                "badges_count": len(badge_points),
                "sessions_logged": len(records),
                "active_days_14d": active_days_14d,
            }
        )

    board.sort(key=lambda row: (row["total_points"], row["sessions_logged"]), reverse=True)
    for idx, row in enumerate(board, start=1):
        row["rank"] = idx
    return board


# =====================================================================
# 6. VIRTUAL COACHING ASSISTANT (DATA-GROUNDED + LIVE ML MODEL ACCESS)
# =====================================================================


def generate_assistant_reply(
    db: Session,
    current_user: User,
    athlete_id: Optional[int],
    user_message: str,
) -> Dict[str, Any]:
    target_id = athlete_id or current_user.id
    target_user = db.query(User).filter(User.id == target_id).first() or current_user
    profile = db.query(AthleteProfile).filter(AthleteProfile.user_id == target_user.id).first()

    recent_preds = (
        db.query(AIPrediction)
        .filter((AIPrediction.athlete_id == target_user.id) | (AIPrediction.requested_by_id == target_user.id))
        .order_by(AIPrediction.created_at.desc())
        .limit(5)
        .all()
    )
    recent_records = (
        db.query(PerformanceRecord)
        .filter(PerformanceRecord.athlete_id == target_user.id)
        .order_by(PerformanceRecord.session_date.desc())
        .limit(5)
        .all()
    )
    active_program = (
        db.query(TrainingProgram)
        .filter(TrainingProgram.athlete_id == target_user.id, TrainingProgram.status == "active")
        .order_by(TrainingProgram.created_at.desc())
        .first()
    )
    latest_risk = (
        db.query(InjuryRiskAssessment)
        .filter(InjuryRiskAssessment.athlete_id == target_user.id)
        .order_by(InjuryRiskAssessment.created_at.desc())
        .first()
    )
    latest_skill = (
        db.query(SkillAssessment)
        .filter(SkillAssessment.athlete_id == target_user.id)
        .order_by(SkillAssessment.created_at.desc())
        .first()
    )

    msg_lower = user_message.lower()
    sources_used: List[str] = []
    sections: List[str] = []

    # 1. Live ML model query detection (e.g., "predict running 45 min at 155 bpm")
    matched_exercise = next((ex for ex in VALID_EXERCISE_TYPES if ex.lower() in msg_lower), None)
    wants_calorie_calc = any(k in msg_lower for k in ["calorie", "kcal", "burn", "predict"]) and (
        matched_exercise is not None or re.search(r"\d+\s*(min|minute|bpm)", msg_lower)
    )
    if wants_calorie_calc:
        dur_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:min|mins|minutes)", msg_lower)
        hr_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:bpm|heart\s*rate)", msg_lower)
        defaults = _safe_athlete_defaults(profile)
        raw = dict(defaults)
        raw["Exercise_Type"] = matched_exercise or (profile.preferred_exercise if profile and profile.preferred_exercise else "Running")
        raw["Duration_Minutes"] = float(dur_m.group(1)) if dur_m else 45.0
        raw["Heart_Rate_BPM"] = float(hr_m.group(1)) if hr_m else 148.0
        if model_service.status == "ready":
            res = model_service.predict_single(raw, include_what_if=False)
            sources_used.append("Trained ExtraTreesRegressor Model (live inference)")
            sections.append(
                f"**Live Trained Model Estimate ({raw['Exercise_Type']}, {raw['Duration_Minutes']:.0f} min @ {raw['Heart_Rate_BPM']:.0f} BPM):**\n"
                f"- Estimated Calories Burned: **{res['predicted_calories']:.1f} kcal** ({res['burn_rate_per_min']:.2f} kcal/min)\n"
                f"- 300-Tree Ensemble 80% Interval: **{res['confidence_low']:.1f} – {res['confidence_high']:.1f} kcal**\n"
                f"- Dataset Peer Rank: **{res['dataset_percentile']}th percentile** for {raw['Exercise_Type']}."
            )
        else:
            sections.append(
                f"The trained calorie model is currently **{model_service.status}**. Once ready, I can compute live estimates directly inside chat."
            )

    # 2. Schedule / training plan queries
    if any(k in msg_lower for k in ["schedule", "plan", "program", "workout", "today", "week"]):
        if active_program:
            sources_used.append(f"Training Program #{active_program.id}")
            sessions = (
                db.query(TrainingSession)
                .filter(TrainingSession.program_id == active_program.id)
                .order_by(TrainingSession.day_index.asc())
                .all()
            )
            done = sum(1 for s in sessions if s.is_completed)
            lines = [
                f"**Active Training Plan — {active_program.title}** ({done}/{len(sessions)} sessions completed):"
            ]
            for s in sessions:
                mark = "[Done]" if s.is_completed else "[Pending]"
                cal_str = f" (~{s.expected_calories:.0f} kcal)" if s.expected_calories else ""
                lines.append(
                    f"- {mark} **{s.day_of_week}:** {s.exercise_type} — {s.focus_area} ({s.target_duration_minutes:.0f} min @ {s.target_heart_rate_bpm:.0f} BPM{cal_str})"
                )
            sections.append("\n".join(lines))
        else:
            sections.append(
                f"No active training program exists yet for **{target_user.full_name}**. Open the **Training Programs** page to generate a personalized weekly schedule."
            )

    # 3. Injury / fatigue / recovery queries
    if any(k in msg_lower for k in ["injury", "risk", "fatigue", "recover", "pain", "sore", "sleep", "acwr"]):
        if latest_risk:
            sources_used.append(f"Injury Risk Assessment #{latest_risk.id}")
            acwr_str = f"{latest_risk.acwr}" if latest_risk.acwr is not None else "N/A"
            factors = "\n".join(f"- {f}" for f in (latest_risk.risk_factors or [])[:3])
            mods = "\n".join(f"- {m}" for m in (latest_risk.training_modifications or [])[:2])
            sections.append(
                f"**Latest Workload Risk Assessment ({latest_risk.risk_level} — {latest_risk.risk_score}/100, ACWR: {acwr_str}):**\n"
                f"{factors}\n**Recommended Adjustments:**\n{mods}\n"
                "_Note: Workload risk indicator only — not a medical diagnosis._"
            )
        else:
            sections.append(
                "No workload injury-risk assessment has been run yet. Log recent sessions and run an assessment on the **Injury Prevention** page for personalized ACWR and recovery guidance."
            )

    # 4. Performance report / prediction history / improvement queries
    if any(k in msg_lower for k in ["report", "performance", "score", "skill", "improv", "progress", "history", "summary", "how am i"]):
        if recent_records:
            sources_used.append(f"{len(recent_records)} Performance Records")
            avg_dur = float(np.mean([r.duration_minutes for r in recent_records]))
            avg_hr = float(np.mean([r.heart_rate_bpm for r in recent_records]))
            sections.append(
                f"**Recent Performance Summary for {target_user.full_name}** ({len(recent_records)} latest sessions):\n"
                f"- Average Duration: **{avg_dur:.1f} min** | Average Heart Rate: **{avg_hr:.0f} BPM**\n"
                f"- Most Recent Workout: **{recent_records[0].exercise_type}** ({recent_records[0].duration_minutes:.0f} min @ {recent_records[0].heart_rate_bpm:.0f} BPM)"
            )
        if recent_preds:
            sources_used.append(f"{len(recent_preds)} AI Predictions")
            p0 = recent_preds[0]
            sections.append(
                f"**Latest Trained Model Prediction:** {p0.exercise_type} ({p0.duration_minutes:.0f} min @ {p0.heart_rate_bpm:.0f} BPM) -> **{p0.predicted_calories:.1f} kcal** ({p0.burn_rate_per_min:.2f} kcal/min)."
            )
        if latest_skill:
            sources_used.append(f"Skill Assessment #{latest_skill.id}")
            sections.append(
                f"**Skill Score:** **{latest_skill.overall_score}/100** (Cohort Rank #{latest_skill.db_cohort_rank}/{latest_skill.db_cohort_total}). "
                f"Top focus to improve: {', '.join(latest_skill.improvement_areas or [])}."
            )
        if not recent_records and not recent_preds and not latest_skill:
            sections.append(
                f"No performance records, AI predictions, or skill scores are logged yet for **{target_user.full_name}**. "
                "Start by running an AI Calorie Prediction or logging a training session!"
            )

    # 5. General fallback grounded in real context
    if not sections:
        context_bits = [
            f"Athlete context: **{target_user.full_name}**",
            f"Logged sessions: **{len(recent_records)}**",
            f"AI predictions: **{len(recent_preds)}**",
            f"Active plan: **{'Yes — ' + active_program.title if active_program else 'None yet'}**",
            f"Latest risk level: **{latest_risk.risk_level if latest_risk else 'Not assessed'}**",
        ]
        sections.append(
            "Here is your live coaching context:\n- "
            + "\n- ".join(context_bits)
            + "\n\nYou can ask me to:\n"
            "- Explain your **performance report** or **skill score**\n"
            "- Review your **weekly training schedule**\n"
            "- Check **injury risk & recovery adjustments**\n"
            "- Run a **live calorie prediction** (e.g., *\"Predict calories for Running 50 minutes at 158 bpm\"*)"
        )
        sources_used.append("Authorized Athlete Database Context")

    return {
        "reply": "\n\n".join(sections),
        "sources": sources_used,
        "athlete_id": target_user.id,
        "athlete_name": target_user.full_name,
    }
