from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.db.database import get_db
from app.db.models import GameStrategy, Opponent, User, UserRole
from app.schemas.schemas import OpponentCreate, StrategyGenerateRequest
from app.services.activity_service import log_activity
from app.services.analytics_service import generate_game_strategy

router = APIRouter(prefix="/api/strategy", tags=["Game Strategy Optimization"])


def _serialize_opponent(o: Opponent) -> dict:
    return {
        "id": o.id,
        "name": o.name,
        "sport": o.sport,
        "team_or_club": o.team_or_club,
        "avg_speed_kmh": o.avg_speed_kmh,
        "endurance_minutes": o.endurance_minutes,
        "win_rate_pct": o.win_rate_pct,
        "offensive_rating": o.offensive_rating,
        "defensive_rating": o.defensive_rating,
        "tempo_style": o.tempo_style,
        "observed_strengths": o.observed_strengths,
        "observed_weaknesses": o.observed_weaknesses,
        "notes": o.notes,
        "created_at": o.created_at.isoformat(),
    }


def _serialize_strategy(s: GameStrategy, opp_name: Optional[str] = None) -> dict:
    return {
        "id": s.id,
        "opponent_id": s.opponent_id,
        "opponent_name": opp_name,
        "athlete_id": s.athlete_id,
        "title": s.title,
        "tactical_summary": s.tactical_summary,
        "counter_strategies": s.counter_strategies or [],
        "comparison_metrics": s.comparison_metrics or {},
        "scenario_simulations": s.scenario_simulations or [],
        "data_availability_notes": s.data_availability_notes or [],
        "created_at": s.created_at.isoformat(),
    }


@router.post("/opponents", status_code=status.HTTP_201_CREATED)
def create_opponent(
    payload: OpponentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    opp = Opponent(created_by_id=current_user.id, **payload.model_dump())
    db.add(opp)
    db.commit()
    db.refresh(opp)
    log_activity(
        db,
        current_user.id,
        "opponent_created",
        "opponent",
        f"Added opponent profile '{opp.name}' ({opp.sport}).",
        entity_id=opp.id,
    )
    return _serialize_opponent(opp)


@router.get("/opponents")
def list_opponents(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    rows = db.query(Opponent).order_by(Opponent.created_at.desc()).all()
    return [_serialize_opponent(r) for r in rows]


@router.delete("/opponents/{opponent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_opponent(
    opponent_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.COACH, UserRole.ANALYST)),
):
    opp = db.query(Opponent).filter(Opponent.id == opponent_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opponent not found.")
    db.delete(opp)
    db.commit()
    return None


@router.post("/generate", status_code=status.HTTP_201_CREATED)
def create_game_strategy(
    payload: StrategyGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    opp = db.query(Opponent).filter(Opponent.id == payload.opponent_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opponent not found.")
    athlete = db.query(User).filter(User.id == payload.athlete_id).first() if payload.athlete_id else None

    strategy = generate_game_strategy(
        db=db,
        opponent=opp,
        created_by=current_user,
        athlete=athlete,
        title=payload.title,
        tempo_adjustment_pct=payload.tempo_adjustment_pct,
        defensive_focus_pct=payload.defensive_focus_pct,
    )
    log_activity(
        db,
        current_user.id,
        "strategy_generated",
        "game_strategy",
        f"Generated tactical game plan '{strategy.title}' vs {opp.name}.",
        entity_id=strategy.id,
    )
    return _serialize_strategy(strategy, opp.name)


@router.get("/plans")
def list_strategies(
    opponent_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    q = db.query(GameStrategy)
    if opponent_id:
        q = q.filter(GameStrategy.opponent_id == opponent_id)
    rows = q.order_by(GameStrategy.created_at.desc()).limit(50).all()
    opps = {o.id: o.name for o in db.query(Opponent).all()}
    return [_serialize_strategy(s, opps.get(s.opponent_id)) for s in rows]
