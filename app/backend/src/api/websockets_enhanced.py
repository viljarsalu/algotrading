"""Enhanced WebSocket endpoints with real-time dYdX data and fallback.

This module provides WebSocket endpoints with real-time dYdX Indexer integration
and automatic fallback to HTTP polling if WebSocket fails.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from ..bot.dydx_client import DydxClient
from ..bot.websocket_manager import WebSocketManager
from ..bot.websocket_handlers import WebSocketHandlers
from ..core.security import get_current_user
from ..core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websockets"])


class EnhancedConnectionManager:
    """Track active dashboard WebSocket connections with real-time support."""

    def __init__(self) -> None:
        self.active_connections: Dict[str, WebSocket] = {}
        self.stream_tasks: Dict[str, asyncio.Task[Any]] = {}
        self.ws_managers: Dict[str, WebSocketManager] = {}

    async def connect(self, websocket: WebSocket, user_address: str) -> None:
        """Connect dashboard client and start dYdX WebSocket listener.

        Args:
            websocket: FastAPI WebSocket connection
            user_address: User's wallet address
        """
        await websocket.accept()
        self.active_connections[user_address] = websocket
        logger.info("WebSocket connected for user %s", user_address)

    def disconnect(self, user_address: str) -> None:
        """Disconnect dashboard client and close dYdX WebSocket.

        Args:
            user_address: User's wallet address
        """
        # Cancel listener task
        task = self.stream_tasks.pop(user_address, None)
        if task and not task.done():
            task.cancel()

        # Close WebSocket manager
        ws_manager = self.ws_managers.pop(user_address, None)
        if ws_manager:
            asyncio.create_task(ws_manager.disconnect())

        self.active_connections.pop(user_address, None)
        logger.info("WebSocket disconnected for user %s", user_address)

    async def send_personal_message(self, message: Dict[str, Any], user_address: str) -> None:
        """Send message to dashboard client.

        Args:
            message: Message to send
            user_address: User's wallet address
        """
        websocket = self.active_connections.get(user_address)
        if not websocket:
            return
        try:
            await websocket.send_json(message)
        except Exception as exc:
            logger.error("Failed to send WebSocket message: %s", exc)

    def register_stream_task(self, user_address: str, task: asyncio.Task[Any]) -> None:
        """Register stream task for user.

        Args:
            user_address: User's wallet address
            task: Asyncio task
        """
        self.stream_tasks[user_address] = task

    def register_ws_manager(self, user_address: str, manager: WebSocketManager) -> None:
        """Register WebSocket manager for user.

        Args:
            user_address: User's wallet address
            manager: WebSocketManager instance
        """
        self.ws_managers[user_address] = manager


manager = EnhancedConnectionManager()


async def _stream_account_state_realtime(user_address: str) -> None:
    """Stream account state using dYdX WebSocket with fallback to HTTP polling.

    Args:
        user_address: User's wallet address
    """
    settings = get_settings()

    # Determine WebSocket URL based on environment
    if settings.env == "production":
        ws_url = "wss://indexer.dydx.trade/v4/ws"
    else:
        ws_url = "wss://indexer.v4testnet.dydx.exchange/v4/ws"

    # Create WebSocket manager
    ws_manager = WebSocketManager(ws_url, user_address)
    manager.register_ws_manager(user_address, ws_manager)

    # Create handlers
    async def on_account_update(data: Dict[str, Any]) -> None:
        """Handle account update."""
        await manager.send_personal_message(
            {
                "type": "account_update",
                "source": "websocket",
                "data": data,
            },
            user_address,
        )

    async def on_order_update(data: Dict[str, Any]) -> None:
        """Handle order update."""
        await manager.send_personal_message(
            {
                "type": "order_update",
                "source": "websocket",
                "data": data,
            },
            user_address,
        )

    async def on_trade_update(data: Dict[str, Any]) -> None:
        """Handle trade update."""
        await manager.send_personal_message(
            {
                "type": "trade_update",
                "source": "websocket",
                "data": data,
            },
            user_address,
        )

    handlers = WebSocketHandlers(
        on_account_update=on_account_update,
        on_order_update=on_order_update,
        on_trade_update=on_trade_update,
    )

    # Register handlers
    await ws_manager.register_handler("v4_subaccounts", handlers.handle_subaccount_update)
    await ws_manager.register_handler("v4_orders", handlers.handle_order_update)
    await ws_manager.register_handler("v4_trades", handlers.handle_trade_update)

    # Subscribe to channels
    await ws_manager.subscribe("v4_subaccounts")
    await ws_manager.subscribe("v4_orders")
    await ws_manager.subscribe("v4_trades")

    # Start listener
    try:
        await ws_manager.listen()
    except Exception as e:
        logger.error("WebSocket listener failed: %s", e)
        logger.info("Falling back to HTTP polling for %s", user_address)
        await _stream_account_state_polling(user_address)


async def _stream_account_state_polling(user_address: str) -> None:
    """Poll dYdX account state and push updates to the dashboard (fallback).

    Args:
        user_address: User's wallet address
    """
    try:
        dydx_client = await DydxClient.create_client()
    except Exception as exc:
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
                        "source": "polling",
                        "success": False,
                        "error": account_snapshot.get("error", "Unknown error"),
                    },
                    user_address,
                )
            else:
                await manager.send_personal_message(
                    {
                        "type": "account_update",
                        "source": "polling",
                        "success": True,
                        "account": account_snapshot.get("account", {}),
                        "positions": account_snapshot.get("positions", []),
                        "subaccount": account_snapshot.get("subaccount", {}),
                    },
                    user_address,
                )
        except asyncio.CancelledError:
            logger.info("Stopping account stream for %s", user_address)
            raise
        except Exception as exc:
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
    """Authenticate and stream account data to the dashboard client.

    Uses real-time WebSocket when available, falls back to HTTP polling.

    Args:
        websocket: FastAPI WebSocket connection
        token: Authentication token
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_address = get_current_user(token)
    if not user_address:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, user_address)

    # Start real-time stream with fallback
    stream_task = asyncio.create_task(_stream_account_state_realtime(user_address))
    manager.register_stream_task(user_address, stream_task)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("Dashboard WebSocket disconnect for %s", user_address)
    except Exception as exc:
        logger.error("WebSocket error for %s: %s", user_address, exc)
    finally:
        manager.disconnect(user_address)
        if stream_task and not stream_task.done():
            stream_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await stream_task


@router.get("/status/{user_address}")
async def get_websocket_status(user_address: str) -> Dict[str, Any]:
    """Get WebSocket connection status for a user.

    Args:
        user_address: User's wallet address

    Returns:
        WebSocket status information
    """
    ws_manager = manager.ws_managers.get(user_address)

    if not ws_manager:
        return {
            "connected": False,
            "user_address": user_address,
            "message": "No active WebSocket connection",
        }

    return {
        "connected": True,
        "user_address": user_address,
        **ws_manager.get_status(),
    }
