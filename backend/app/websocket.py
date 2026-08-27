import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections.
    Broadcasts live MQTT payloads to all connected dashboard clients.
    """

    def __init__(self):
        # Maps websocket → user_id (or None for unauthenticated connections)
        self.active: Dict[WebSocket, int | None] = {}

    async def connect(self, ws: WebSocket, user_id: int | None = None):
        await ws.accept()
        self.active[ws] = user_id
        logger.info(f"WS connected. Total clients: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        self.active.pop(ws, None)
        logger.info(f"WS disconnected. Total clients: {len(self.active)}")

    async def broadcast(self, data: dict):
        """Send a JSON message to every connected client."""
        message = json.dumps(data, default=str)
        dead: Set[WebSocket] = set()
        for ws in list(self.active):
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_to(self, ws: WebSocket, data: dict):
        """Send a JSON message to a single client."""
        try:
            await ws.send_text(json.dumps(data, default=str))
        except Exception:
            self.disconnect(ws)

    @property
    def client_count(self) -> int:
        return len(self.active)


# Singleton — imported by main.py, mqtt.py, and the WebSocket router
manager = ConnectionManager()
