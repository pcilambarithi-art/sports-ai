from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.db.database import get_db
from app.db.models import AthleteProfile, CoachProfile, User, UserRole
from app.schemas.schemas import LoginRequest, RegisterRequest
from app.services.activity_service import log_activity

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def serialize_user(user: User) -> dict:
    role_val = user.role.value if isinstance(user.role, UserRole) else str(user.role)
    data = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": role_val,
        "is_active": user.is_active,
        "avatar_initials": user.avatar_initials
        or "".join(part[0].upper() for part in user.full_name.split()[:2]),
        "bio": user.bio,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "athlete_profile": None,
        "coach_profile": None,
    }
    if user.athlete_profile:
        ap = user.athlete_profile
        data["athlete_profile"] = {
            "sport": ap.sport,
            "position": ap.position,
            "age": ap.age,
            "gender": ap.gender,
            "weight_kg": ap.weight_kg,
            "height_cm": ap.height_cm,
            "experience_level": ap.experience_level,
            "fitness_goal": ap.fitness_goal,
            "preferred_exercise": ap.preferred_exercise,
            "workout_frequency_per_week": ap.workout_frequency_per_week,
            "avg_sleep_hours": ap.avg_sleep_hours,
            "avg_water_intake_liters": ap.avg_water_intake_liters,
            "resting_heart_rate": ap.resting_heart_rate,
        }
    if user.coach_profile:
        cp = user.coach_profile
        data["coach_profile"] = {
            "specialization": cp.specialization,
            "certifications": cp.certifications,
            "years_experience": cp.years_experience,
            "team_name": cp.team_name,
        }
    return data


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email_norm = payload.email.strip().lower()
    if db.query(User).filter(User.email == email_norm).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    role_enum = UserRole(payload.role)
    initials = "".join(p[0].upper() for p in payload.full_name.strip().split()[:2]) or "U"
    user = User(
        email=email_norm,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=role_enum,
        avatar_initials=initials[:4],
    )
    db.add(user)
    db.flush()

    if role_enum == UserRole.ATHLETE:
        db.add(AthleteProfile(user_id=user.id, sport=payload.sport))
    elif role_enum == UserRole.COACH:
        db.add(CoachProfile(user_id=user.id, specialization=payload.sport))

    db.commit()
    db.refresh(user)

    log_activity(
        db,
        user.id,
        "user_registered",
        "user",
        f"{user.full_name} registered as {role_enum.value}.",
        entity_id=user.id,
    )

    token = create_access_token(subject=str(user.id), role=role_enum.value)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email_norm = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_norm).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated by an administrator.",
        )

    role_val = user.role.value if isinstance(user.role, UserRole) else str(user.role)
    token = create_access_token(subject=str(user.id), role=role_val)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)
