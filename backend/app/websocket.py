# app/websocket.py

import json
import logging
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections and broadcasts
    live readings to connected dashboard clients.
    """

    def __init__(self):
        self.active: Dict[
            WebSocket,
            int | None
        ] = {}

    async def connect(
        self,
        ws: WebSocket,
        user_id: int | None = None,
    ):
        await ws.accept()

        self.active[ws] = user_id

        logger.info(
            "WS connected. Total clients: %s",
            len(self.active),
        )

    def disconnect(
        self,
        ws: WebSocket,
    ):
        self.active.pop(
            ws,
            None,
        )

        logger.info(
            "WS disconnected. Total clients: %s",
            len(self.active),
        )

    async def broadcast(
        self,
        data: dict,
    ):
        """
        Send a JSON message to every connected client.
        """

        message = json.dumps(
            data,
            default=str,
        )

        dead: Set[WebSocket] = set()

        for ws in list(
            self.active
        ):

            try:

                await ws.send_text(
                    message
                )

                logger.debug(
                    "WebSocket message sent successfully."
                )

            except Exception:

                logger.exception(
                    "Failed to send WebSocket message."
                )

                dead.add(ws)

        for ws in dead:
            self.disconnect(ws)

    async def send_to(
        self,
        ws: WebSocket,
        data: dict,
    ):
        """
        Send a JSON message to one client.
        """

        try:

            await ws.send_text(
                json.dumps(
                    data,
                    default=str,
                )
            )

        except Exception:

            logger.exception(
                "Failed to send WebSocket message."
            )

            self.disconnect(ws)

    @property
    def client_count(self) -> int:
        return len(
            self.active
        )


manager = ConnectionManager()
