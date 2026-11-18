from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import can_access_athlete, decode_access_token, get_current_user
from app.db.database import get_db
from app.db.models import TelemetryReading, User
from app.schemas.schemas import TelemetryIngestRequest
from app.services.ws_manager import telemetry_ws_manager

router = APIRouter(prefix="/api/telemetry", tags=["Real-Time Performance Tracking"])


def _serialize_reading(r: TelemetryReading) -> dict:
    return {
        "id": r.id,
        "athlete_id": r.athlete_id,
        "source_type": r.source_type,
        "device_name": r.device_name,
        "heart_rate_bpm": r.heart_rate_bpm,
        "speed_kmh": r.speed_kmh,
        "distance_km": r.distance_km,
        "duration_minutes": r.duration_minutes,
        "calories": r.calories,
        "muscle_load_pct": r.muscle_load_pct,
        "fatigue_index": r.fatigue_index,
        "recorded_at": r.recorded_at.isoformat(),
    }


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest_telemetry(
    payload: TelemetryIngestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ingest real telemetry reading from an authenticated athlete/coach or connected browser client."""
    target_id = payload.athlete_id or current_user.id
    if not can_access_athlete(current_user, target_id, db):
        raise HTTPException(status_code=403, detail="Access denied for this athlete.")

    reading = TelemetryReading(
        athlete_id=target_id,
        source_type=payload.source_type,
        device_name=payload.device_name or "Manual Entry",
        heart_rate_bpm=payload.heart_rate_bpm,
        speed_kmh=payload.speed_kmh,
        distance_km=payload.distance_km,
        duration_minutes=payload.duration_minutes,
        calories=payload.calories,
        muscle_load_pct=payload.muscle_load_pct,
        fatigue_index=payload.fatigue_index,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    data = _serialize_reading(reading)
    await telemetry_ws_manager.broadcast(target_id, {"event": "telemetry_update", "reading": data})
    return data


@router.post("/webhook", status_code=status.HTTP_201_CREATED)
async def ingest_sensor_webhook(
    payload: TelemetryIngestRequest,
    x_sensor_api_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    """External wearable / IoT sensor webhook endpoint secured by X-Sensor-API-Key header."""
    if not x_sensor_api_key or x_sensor_api_key != settings.SENSOR_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Sensor-API-Key header.")
    if not payload.athlete_id:
        raise HTTPException(status_code=400, detail="athlete_id is required for wearable webhook ingestion.")

    athlete = db.query(User).filter(User.id == payload.athlete_id).first()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found.")

    reading = TelemetryReading(
        athlete_id=payload.athlete_id,
        source_type=payload.source_type if payload.source_type != "manual" else "wearable_webhook",
        device_name=payload.device_name or "External Wearable Sensor",
        heart_rate_bpm=payload.heart_rate_bpm,
        speed_kmh=payload.speed_kmh,
        distance_km=payload.distance_km,
        duration_minutes=payload.duration_minutes,
        calories=payload.calories,
        muscle_load_pct=payload.muscle_load_pct,
        fatigue_index=payload.fatigue_index,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    data = _serialize_reading(reading)
    await telemetry_ws_manager.broadcast(payload.athlete_id, {"event": "telemetry_update", "reading": data})
    return data


@router.get("/status")
def get_telemetry_status(
    athlete_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Honestly report whether an active wearable/IoT hardware stream is connected."""
    target_id = athlete_id or current_user.id
    if not can_access_athlete(current_user, target_id, db):
        raise HTTPException(status_code=403, detail="Access denied.")

    recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    latest_sensor = (
        db.query(TelemetryReading)
        .filter(
            TelemetryReading.athlete_id == target_id,
            TelemetryReading.source_type.in_(["wearable_webhook", "iot_sensor"]),
        )
        .order_by(TelemetryReading.recorded_at.desc())
        .first()
    )
    latest_any = (
        db.query(TelemetryReading)
        .filter(TelemetryReading.athlete_id == target_id)
        .order_by(TelemetryReading.recorded_at.desc())
        .first()
    )

    hardware_connected = False
    if latest_sensor:
        ts = latest_sensor.recorded_at
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        hardware_connected = ts >= recent_cutoff

    return {
        "athlete_id": target_id,
        "hardware_connected": hardware_connected,
        "status_label": (
            f"Live Sensor Connected ({latest_sensor.device_name})"
            if hardware_connected and latest_sensor
            else "Awaiting Wearable / IoT Sensor Integration"
        ),
        "websocket_subscribers": telemetry_ws_manager.active_subscriber_count(target_id),
        "latest_reading": _serialize_reading(latest_any) if latest_any else None,
        "webhook_endpoint": "/api/telemetry/webhook",
    }


@router.get("/history")
def get_telemetry_history(
    athlete_id: Optional[int] = Query(default=None),
    limit: int = Query(default=60, ge=1, le=300),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_id = athlete_id or current_user.id
    if not can_access_athlete(current_user, target_id, db):
        raise HTTPException(status_code=403, detail="Access denied.")

    rows = (
        db.query(TelemetryReading)
        .filter(TelemetryReading.athlete_id == target_id)
        .order_by(TelemetryReading.recorded_at.desc())
        .limit(limit)
        .all()
    )
    return [_serialize_reading(r) for r in reversed(rows)]


@router.websocket("/ws/{athlete_id}")
async def telemetry_websocket(
    websocket: WebSocket,
    athlete_id: int,
    token: Optional[str] = Query(default=None),
):
    if not token:
        await websocket.close(code=4401)
        return
    try:
        decode_access_token(token)
    except HTTPException:
        await websocket.close(code=4401)
        return

    await telemetry_ws_manager.connect(athlete_id, websocket)
    try:
        await websocket.send_json(
            {
                "event": "connected",
                "athlete_id": athlete_id,
                "message": "Subscribed to real-time telemetry stream.",
            }
        )
        while True:
            # Keep connection alive; wait for client ping/keepalive
            await websocket.receive_text()
    except WebSocketDisconnect:
        telemetry_ws_manager.disconnect(athlete_id, websocket)
    except Exception:
        telemetry_ws_manager.disconnect(athlete_id, websocket)
