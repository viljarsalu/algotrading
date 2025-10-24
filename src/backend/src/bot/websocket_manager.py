"""WebSocket Manager - Real-time dYdX Data Streaming.

This module manages WebSocket connections to dYdX Indexer for real-time
account, order, and trade updates with automatic reconnection and fallback.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections with automatic reconnection."""

    def __init__(
        self,
        ws_url: str,
        user_address: str,
        max_reconnect_attempts: int = 5,
        initial_backoff: float = 1.0,
        max_backoff: float = 16.0,
    ):
        """Initialize WebSocket manager.

        Args:
            ws_url: WebSocket URL (testnet or mainnet)
            user_address: User's wallet address
            max_reconnect_attempts: Maximum reconnection attempts
            initial_backoff: Initial backoff delay in seconds
            max_backoff: Maximum backoff delay in seconds
        """
        self.ws_url = ws_url
        self.user_address = user_address
        self.max_reconnect_attempts = max_reconnect_attempts
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff

        self.websocket = None
        self.is_connected = False
        self.reconnect_count = 0
        self.subscriptions = set()
        self.message_handlers: Dict[str, Callable] = {}
        self.last_heartbeat = None
        self._listener_task = None

    async def connect(self) -> bool:
        """Establish WebSocket connection with retry logic.

        Returns:
            True if connection successful, False otherwise
        """
        import websockets

        backoff = self.initial_backoff

        for attempt in range(self.max_reconnect_attempts):
            try:
                self.websocket = await websockets.connect(self.ws_url)
                self.is_connected = True
                self.reconnect_count = 0
                logger.info(
                    f"WebSocket connected to {self.ws_url} (attempt {attempt + 1})"
                )

                # Resubscribe to channels
                await self._resubscribe()

                return True

            except Exception as e:
                logger.warning(
                    f"Connection attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {backoff}s..."
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, self.max_backoff)

        logger.error(
            f"Failed to connect after {self.max_reconnect_attempts} attempts"
        )
        self.is_connected = False
        return False

    async def disconnect(self) -> None:
        """Close WebSocket connection gracefully."""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
            self.is_connected = False
            logger.info("WebSocket disconnected")

    async def subscribe(self, channel: str) -> None:
        """Subscribe to a channel.

        Args:
            channel: Channel name (v4_subaccounts, v4_orders, v4_trades, etc.)
        """
        if not self.is_connected:
            logger.warning(f"Cannot subscribe to {channel}: not connected")
            self.subscriptions.add(channel)  # Add for later resubscription
            return

        subscription = {
            "type": "subscribe",
            "channel": channel,
            "id": self.user_address,
        }

        try:
            await self.websocket.send(json.dumps(subscription))
            self.subscriptions.add(channel)
            logger.info(f"Subscribed to {channel}")
        except Exception as e:
            logger.error(f"Failed to subscribe to {channel}: {e}")

    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from a channel.

        Args:
            channel: Channel name
        """
        if not self.is_connected:
            self.subscriptions.discard(channel)
            return

        unsubscription = {
            "type": "unsubscribe",
            "channel": channel,
            "id": self.user_address,
        }

        try:
            await self.websocket.send(json.dumps(unsubscription))
            self.subscriptions.discard(channel)
            logger.info(f"Unsubscribed from {channel}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe from {channel}: {e}")

    async def _resubscribe(self) -> None:
        """Resubscribe to all channels after reconnection."""
        for channel in self.subscriptions:
            await self.subscribe(channel)

    async def register_handler(self, channel: str, handler: Callable) -> None:
        """Register message handler for a channel.

        Args:
            channel: Channel name
            handler: Async function to handle messages
        """
        self.message_handlers[channel] = handler
        logger.info(f"Registered handler for {channel}")

    async def listen(self) -> None:
        """Listen for WebSocket messages with automatic reconnection."""
        while True:
            try:
                if not self.is_connected:
                    if not await self.connect():
                        await asyncio.sleep(5)
                        continue

                async for message in self.websocket:
                    try:
                        data = json.loads(message)

                        # Handle heartbeat
                        if data.get("type") == "ping":
                            await self._handle_ping()
                            continue

                        # Handle subscription confirmation
                        if data.get("type") == "subscribed":
                            logger.debug(
                                f"Subscribed to {data.get('channel')}"
                            )
                            continue

                        # Handle unsubscription confirmation
                        if data.get("type") == "unsubscribed":
                            logger.debug(
                                f"Unsubscribed from {data.get('channel')}"
                            )
                            continue

                        # Route to appropriate handler
                        channel = data.get("channel")
                        if channel in self.message_handlers:
                            handler = self.message_handlers[channel]
                            try:
                                await handler(data)
                            except Exception as e:
                                logger.error(
                                    f"Error in handler for {channel}: {e}"
                                )

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse WebSocket message: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")

            except Exception as e:
                logger.error(f"Error in WebSocket listener: {e}")
                self.is_connected = False
                await asyncio.sleep(1)

    async def _handle_ping(self) -> None:
        """Handle heartbeat ping from server."""
        try:
            pong = {"type": "pong"}
            await self.websocket.send(json.dumps(pong))
            self.last_heartbeat = datetime.utcnow()
            logger.debug("Sent pong response")
        except Exception as e:
            logger.error(f"Failed to send pong: {e}")

    def is_healthy(self) -> bool:
        """Check if WebSocket connection is healthy.

        Returns:
            True if connected and recent heartbeat, False otherwise
        """
        if not self.is_connected:
            return False

        # Check if we've received a heartbeat recently (within 60 seconds)
        if self.last_heartbeat:
            time_since_heartbeat = (
                datetime.utcnow() - self.last_heartbeat
            ).total_seconds()
            if time_since_heartbeat > 60:
                logger.warning(
                    f"No heartbeat for {time_since_heartbeat:.0f} seconds"
                )
                return False

        return True

    def get_status(self) -> Dict[str, Any]:
        """Get WebSocket connection status.

        Returns:
            Dictionary with status information
        """
        return {
            "is_connected": self.is_connected,
            "is_healthy": self.is_healthy(),
            "ws_url": self.ws_url,
            "user_address": self.user_address,
            "subscriptions": list(self.subscriptions),
            "handlers_registered": len(self.message_handlers),
            "reconnect_count": self.reconnect_count,
            "last_heartbeat": (
                self.last_heartbeat.isoformat()
                if self.last_heartbeat
                else None
            ),
        }
