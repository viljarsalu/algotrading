"""WebSocket endpoints for real-time dYdX dashboard updates."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from ..bot.dydx_client import DydxClient
from ..core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websockets"])


class ConnectionManager:
    """Track active dashboard WebSocket connections."""

    def __init__(self) -> None:
        self.active_connections: Dict[str, WebSocket] = {}
        self.stream_tasks: Dict[str, asyncio.Task[Any]] = {}

    async def connect(self, websocket: WebSocket, user_address: str) -> None:
        await websocket.accept()
        self.active_connections[user_address] = websocket
        logger.info("WebSocket connected for user %s", user_address)

    def disconnect(self, user_address: str) -> None:
        task = self.stream_tasks.pop(user_address, None)
        if task and not task.done():
            task.cancel()
        self.active_connections.pop(user_address, None)
        logger.info("WebSocket disconnected for user %s", user_address)

    async def send_personal_message(self, message: Dict[str, Any], user_address: str) -> None:
        websocket = self.active_connections.get(user_address)
        if not websocket:
            return
        try:
            await websocket.send_json(message)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send WebSocket message: %s", exc)

    def register_stream_task(self, user_address: str, task: asyncio.Task[Any]) -> None:
        self.stream_tasks[user_address] = task


manager = ConnectionManager()


async def _stream_account_state(user_address: str) -> None:
    """Poll dYdX account state and push updates to the dashboard."""

    try:
        dydx_client = await DydxClient.create_client()
    except Exception as exc:  # noqa: BLE001
        logger.error("Unable to initialise dYdX client for %s: %s", user_address, exc)
        await manager.send_personal_message(
            {
                "type": "error",
                "message": "Failed to initialise dYdX client",
                "details": str(exc),
            },
            user_address,
        )
        return

    poll_interval = 15.0

    while True:
        try:
            account_snapshot = await DydxClient.get_account_info(dydx_client)
            if not account_snapshot.get("success", False):
                await manager.send_personal_message(
                    {
                        "type": "account_update",
                        "success": False,
                        "error": account_snapshot.get("error", "Unknown error"),
                    },
                    user_address,
                )
            else:
                await manager.send_personal_message(
                    {
                        "type": "account_update",
                        "success": True,
                        "account": account_snapshot.get("account", {}),
                        "positions": account_snapshot.get("positions", []),
                        "subaccount": account_snapshot.get("subaccount", {}),
                    },
                    user_address,
                )
        except asyncio.CancelledError:  # noqa: PERF203
            logger.info("Stopping account stream for %s", user_address)
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception("Account streaming error for %s: %s", user_address, exc)
            await manager.send_personal_message(
                {
                    "type": "error",
                    "message": "Error fetching account data",
                    "details": str(exc),
                },
                user_address,
            )

        await asyncio.sleep(poll_interval)


@router.websocket("/dashboard")
async def dashboard_stream(websocket: WebSocket, token: Optional[str] = None) -> None:
    """Authenticate and stream account data to the dashboard client."""

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_address = get_current_user(token)
    if not user_address:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, user_address)

    stream_task = asyncio.create_task(_stream_account_state(user_address))
    manager.register_stream_task(user_address, stream_task)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("Dashboard WebSocket disconnect for %s", user_address)
    except Exception as exc:  # noqa: BLE001
        logger.error("WebSocket error for %s: %s", user_address, exc)
    finally:
        manager.disconnect(user_address)
        if stream_task and not stream_task.done():
            stream_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await stream_task
