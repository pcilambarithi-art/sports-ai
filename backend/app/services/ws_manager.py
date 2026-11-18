from typing import Dict, Set
from fastapi import WebSocket


class TelemetryConnectionManager:
    """Manages real-time WebSocket subscribers for athlete telemetry streams."""

    def __init__(self) -> None:
        self._connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, athlete_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(athlete_id, set()).add(websocket)

    def disconnect(self, athlete_id: int, websocket: WebSocket) -> None:
        conns = self._connections.get(athlete_id)
        if conns:
            conns.discard(websocket)
            if not conns:
                self._connections.pop(athlete_id, None)

    async def broadcast(self, athlete_id: int, payload: dict) -> None:
        conns = list(self._connections.get(athlete_id, set()))
        dead = []
        for ws in conns:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(athlete_id, ws)

    def active_subscriber_count(self, athlete_id: int | None = None) -> int:
        if athlete_id is not None:
            return len(self._connections.get(athlete_id, set()))
        return sum(len(s) for s in self._connections.values())


telemetry_ws_manager = TelemetryConnectionManager()
