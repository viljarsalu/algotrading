# WebSocket Integration Guide - dYdX Real-time Data

## Overview

This guide provides code examples for integrating dYdX Indexer WebSocket API for real-time account, order, and trade updates. The WebSocket API provides instant notifications instead of HTTP polling.

## dYdX WebSocket Channels

### Available Channels

1. **v4_subaccounts** - Account balance and position changes
2. **v4_orders** - Order status updates (placed, filled, cancelled, etc.)
3. **v4_trades** - Trade fill notifications
4. **v4_candles** - OHLCV candlestick data
5. **v4_orderbook** - Order book updates

## WebSocket Connection URLs

```python
# Testnet
TESTNET_WS_URL = "wss://indexer.v4testnet.dydx.exchange/v4/ws"

# Mainnet
MAINNET_WS_URL = "wss://indexer.dydx.trade/v4/ws"
```

---

## Example 1: Basic WebSocket Connection

```python
import asyncio
import json
import logging
import websockets
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class DydxWebSocketClient:
    """Basic dYdX WebSocket client for real-time data."""

    def __init__(self, ws_url: str, user_address: str):
        """
        Initialize WebSocket client.

        Args:
            ws_url: WebSocket URL (testnet or mainnet)
            user_address: User's dYdX wallet address
        """
        self.ws_url = ws_url
        self.user_address = user_address
        self.websocket = None
        self.is_connected = False

    async def connect(self) -> None:
        """Establish WebSocket connection."""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.is_connected = True
            logger.info(f"WebSocket connected to {self.ws_url}")
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            raise

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("WebSocket disconnected")

    async def subscribe_to_subaccounts(self) -> None:
        """Subscribe to subaccount updates."""
        subscription = {
            "type": "subscribe",
            "channel": "v4_subaccounts",
            "id": self.user_address,
        }
        await self.websocket.send(json.dumps(subscription))
        logger.info(f"Subscribed to v4_subaccounts for {self.user_address}")

    async def subscribe_to_orders(self) -> None:
        """Subscribe to order updates."""
        subscription = {
            "type": "subscribe",
            "channel": "v4_orders",
            "id": self.user_address,
        }
        await self.websocket.send(json.dumps(subscription))
        logger.info(f"Subscribed to v4_orders for {self.user_address}")

    async def subscribe_to_trades(self) -> None:
        """Subscribe to trade updates."""
        subscription = {
            "type": "subscribe",
            "channel": "v4_trades",
            "id": self.user_address,
        }
        await self.websocket.send(json.dumps(subscription))
        logger.info(f"Subscribed to v4_trades for {self.user_address}")

    async def listen(self, message_handler: Callable) -> None:
        """
        Listen for WebSocket messages.

        Args:
            message_handler: Async function to handle incoming messages
        """
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await message_handler(data)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error in WebSocket listener: {e}")
            raise
```

---

## Example 2: WebSocket Manager with Reconnection

```python
import asyncio
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
        """
        Initialize WebSocket manager.

        Args:
            ws_url: WebSocket URL
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

    async def connect(self) -> bool:
        """
        Establish WebSocket connection with retry logic.

        Returns:
            True if connection successful, False otherwise
        """
        backoff = self.initial_backoff

        for attempt in range(self.max_reconnect_attempts):
            try:
                import websockets

                self.websocket = await websockets.connect(self.ws_url)
                self.is_connected = True
                self.reconnect_count = 0
                logger.info(f"WebSocket connected (attempt {attempt + 1})")

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
            await self.websocket.close()
            self.is_connected = False
            logger.info("WebSocket disconnected")

    async def subscribe(self, channel: str) -> None:
        """
        Subscribe to a channel.

        Args:
            channel: Channel name (v4_subaccounts, v4_orders, v4_trades, etc.)
        """
        if not self.is_connected:
            logger.warning(f"Cannot subscribe to {channel}: not connected")
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
        """
        Unsubscribe from a channel.

        Args:
            channel: Channel name
        """
        if not self.is_connected:
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
        """
        Register message handler for a channel.

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
                    data = json.loads(message)

                    # Handle heartbeat
                    if data.get("type") == "ping":
                        await self._handle_ping()
                        continue

                    # Handle subscription confirmation
                    if data.get("type") == "subscribed":
                        logger.info(f"Subscribed to {data.get('channel')}")
                        continue

                    # Route to appropriate handler
                    channel = data.get("channel")
                    if channel in self.message_handlers:
                        handler = self.message_handlers[channel]
                        await handler(data)

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
        except Exception as e:
            logger.error(f"Failed to send pong: {e}")
```

---

## Example 3: Message Handlers

```python
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def handle_subaccount_update(message: Dict[str, Any]) -> None:
    """
    Handle subaccount (account balance) updates.

    Message format:
    {
        "type": "channel_data",
        "channel": "v4_subaccounts",
        "id": "user_address",
        "contents": {
            "subaccount": {
                "address": "dydx1...",
                "subaccountNumber": 0,
                "equity": "1000000000",
                "freeCollateral": "500000000",
                "openNotional": "500000000",
                "marginUsed": "500000000"
            }
        }
    }
    """
    try:
        subaccount = message.get("contents", {}).get("subaccount", {})
        equity = float(subaccount.get("equity", 0)) / 1e6
        free_collateral = float(subaccount.get("freeCollateral", 0)) / 1e6

        logger.info(
            f"Account Update - Equity: ${equity:.2f}, "
            f"Free Collateral: ${free_collateral:.2f}"
        )

        # Update dashboard or database here
        # await update_dashboard_balance(equity, free_collateral)

    except Exception as e:
        logger.error(f"Error handling subaccount update: {e}")


async def handle_order_update(message: Dict[str, Any]) -> None:
    """
    Handle order status updates.

    Message format:
    {
        "type": "channel_data",
        "channel": "v4_orders",
        "id": "user_address",
        "contents": {
            "orders": [
                {
                    "id": "order_id",
                    "subaccountNumber": 0,
                    "clientId": "client_id",
                    "clobPairId": "1",
                    "side": "BUY",
                    "quantums": "1000000",
                    "subticks": "50000",
                    "goodTilBlock": 1000000,
                    "orderFlags": "0",
                    "timeInForce": "GTT",
                    "reduceOnly": false,
                    "postOnly": false,
                    "clientMetadata": "0",
                    "status": "OPEN",
                    "createdAtHeight": 1000,
                    "updatedAt": "2024-01-01T00:00:00Z",
                    "updatedAtHeight": 1000
                }
            ]
        }
    }
    """
    try:
        orders = message.get("contents", {}).get("orders", [])

        for order in orders:
            order_id = order.get("id")
            status = order.get("status")
            side = order.get("side")
            size = int(order.get("quantums", 0)) / 1e6
            price = int(order.get("subticks", 0)) / 1e6

            logger.info(
                f"Order Update - ID: {order_id}, Status: {status}, "
                f"Side: {side}, Size: {size}, Price: {price}"
            )

            # Update dashboard or database here
            # await update_dashboard_order(order_id, status, side, size, price)

    except Exception as e:
        logger.error(f"Error handling order update: {e}")


async def handle_trade_update(message: Dict[str, Any]) -> None:
    """
    Handle trade fill updates.

    Message format:
    {
        "type": "channel_data",
        "channel": "v4_trades",
        "id": "user_address",
        "contents": {
            "trades": [
                {
                    "id": "trade_id",
                    "side": "BUY",
                    "size": "1000000",
                    "price": "50000",
                    "createdAt": "2024-01-01T00:00:00Z",
                    "createdAtHeight": 1000
                }
            ]
        }
    }
    """
    try:
        trades = message.get("contents", {}).get("trades", [])

        for trade in trades:
            trade_id = trade.get("id")
            side = trade.get("side")
            size = int(trade.get("size", 0)) / 1e6
            price = int(trade.get("price", 0)) / 1e6
            timestamp = trade.get("createdAt")

            logger.info(
                f"Trade Fill - ID: {trade_id}, Side: {side}, "
                f"Size: {size}, Price: {price}, Time: {timestamp}"
            )

            # Update dashboard or database here
            # await update_dashboard_trade(trade_id, side, size, price, timestamp)

    except Exception as e:
        logger.error(f"Error handling trade update: {e}")
```

---

## Example 4: Integration with FastAPI

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import logging

logger = logging.getLogger(__name__)


class DashboardConnectionManager:
    """Manages WebSocket connections for dashboard clients."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.ws_managers: Dict[str, WebSocketManager] = {}
        self.listener_tasks: Dict[str, asyncio.Task] = {}

    async def connect(
        self, websocket: WebSocket, user_address: str, ws_url: str
    ) -> None:
        """
        Connect dashboard client and start dYdX WebSocket listener.

        Args:
            websocket: FastAPI WebSocket connection
            user_address: User's wallet address
            ws_url: dYdX WebSocket URL
        """
        await websocket.accept()
        self.active_connections[user_address] = websocket

        # Create WebSocket manager for dYdX
        ws_manager = WebSocketManager(ws_url, user_address)

        # Register message handlers
        await ws_manager.register_handler(
            "v4_subaccounts", self._handle_subaccount_update
        )
        await ws_manager.register_handler(
            "v4_orders", self._handle_order_update
        )
        await ws_manager.register_handler(
            "v4_trades", self._handle_trade_update
        )

        self.ws_managers[user_address] = ws_manager

        # Subscribe to channels
        await ws_manager.subscribe("v4_subaccounts")
        await ws_manager.subscribe("v4_orders")
        await ws_manager.subscribe("v4_trades")

        # Start listener task
        listener_task = asyncio.create_task(ws_manager.listen())
        self.listener_tasks[user_address] = listener_task

        logger.info(f"Dashboard connected for {user_address}")

    def disconnect(self, user_address: str) -> None:
        """
        Disconnect dashboard client and close dYdX WebSocket.

        Args:
            user_address: User's wallet address
        """
        self.active_connections.pop(user_address, None)

        # Cancel listener task
        task = self.listener_tasks.pop(user_address, None)
        if task:
            task.cancel()

        # Close WebSocket manager
        ws_manager = self.ws_managers.pop(user_address, None)
        if ws_manager:
            asyncio.create_task(ws_manager.disconnect())

        logger.info(f"Dashboard disconnected for {user_address}")

    async def send_to_dashboard(
        self, user_address: str, message: Dict[str, Any]
    ) -> None:
        """
        Send message to dashboard client.

        Args:
            user_address: User's wallet address
            message: Message to send
        """
        websocket = self.active_connections.get(user_address)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {user_address}: {e}")

    async def _handle_subaccount_update(self, message: Dict[str, Any]) -> None:
        """Handle subaccount update and forward to dashboard."""
        user_address = message.get("id")
        await self.send_to_dashboard(
            user_address,
            {
                "type": "account_update",
                "data": message.get("contents", {}),
            },
        )

    async def _handle_order_update(self, message: Dict[str, Any]) -> None:
        """Handle order update and forward to dashboard."""
        user_address = message.get("id")
        await self.send_to_dashboard(
            user_address,
            {
                "type": "order_update",
                "data": message.get("contents", {}),
            },
        )

    async def _handle_trade_update(self, message: Dict[str, Any]) -> None:
        """Handle trade update and forward to dashboard."""
        user_address = message.get("id")
        await self.send_to_dashboard(
            user_address,
            {
                "type": "trade_update",
                "data": message.get("contents", {}),
            },
        )


# Global connection manager
dashboard_manager = DashboardConnectionManager()


# FastAPI WebSocket endpoint
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for dashboard real-time updates.

    Args:
        websocket: FastAPI WebSocket connection
        token: Authentication token
    """
    # Verify token and get user address
    user_address = verify_token(token)
    if not user_address:
        await websocket.close(code=1008)
        return

    # Connect to dYdX WebSocket
    ws_url = "wss://indexer.v4testnet.dydx.exchange/v4/ws"  # or mainnet
    await dashboard_manager.connect(websocket, user_address, ws_url)

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        dashboard_manager.disconnect(user_address)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        dashboard_manager.disconnect(user_address)
```

---

## Best Practices

### 1. Connection Management
- Always implement reconnection logic with exponential backoff
- Handle heartbeat ping/pong messages
- Gracefully close connections on shutdown

### 2. Error Handling
- Catch and log all exceptions
- Implement fallback to HTTP polling if WebSocket fails
- Provide user feedback on connection status

### 3. Performance
- Use async/await for non-blocking operations
- Batch message processing when possible
- Implement rate limiting for message handlers

### 4. Security
- Validate user address in subscriptions
- Use WSS (secure WebSocket) in production
- Implement proper authentication before connecting

### 5. Testing
- Mock WebSocket connections in tests
- Test reconnection logic
- Test message parsing and handling
- Test fallback mechanisms

---

## Troubleshooting

### Connection Issues
- Check WebSocket URL is correct for network (testnet vs mainnet)
- Verify user address format
- Check firewall/proxy settings

### Message Parsing Errors
- Log raw message before parsing
- Validate message structure
- Handle missing fields gracefully

### Performance Issues
- Monitor message throughput
- Implement message batching
- Consider using separate WebSocket per channel

### Reconnection Loops
- Implement maximum reconnection attempts
- Add jitter to backoff delays
- Log reconnection failures for debugging
