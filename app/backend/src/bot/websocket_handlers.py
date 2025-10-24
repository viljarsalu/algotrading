"""WebSocket Message Handlers - Real-time dYdX Data Processing.

This module contains message handlers for processing real-time updates from
dYdX WebSocket feeds (accounts, orders, trades).
"""

import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketHandlers:
    """Collection of WebSocket message handlers."""

    def __init__(self, on_account_update: Optional[Callable] = None,
                 on_order_update: Optional[Callable] = None,
                 on_trade_update: Optional[Callable] = None):
        """Initialize handlers with optional callbacks.

        Args:
            on_account_update: Callback for account updates
            on_order_update: Callback for order updates
            on_trade_update: Callback for trade updates
        """
        self.on_account_update = on_account_update
        self.on_order_update = on_order_update
        self.on_trade_update = on_trade_update

    async def handle_subaccount_update(self, message: Dict[str, Any]) -> None:
        """Handle subaccount (account balance) updates.

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

        Args:
            message: WebSocket message data
        """
        try:
            subaccount = message.get("contents", {}).get("subaccount", {})
            
            # Convert quantums to tokens (1 token = 1e6 quantums)
            equity = float(subaccount.get("equity", 0)) / 1e6
            free_collateral = float(subaccount.get("freeCollateral", 0)) / 1e6
            margin_used = float(subaccount.get("marginUsed", 0)) / 1e6

            account_data = {
                "address": subaccount.get("address"),
                "subaccount_number": subaccount.get("subaccountNumber"),
                "equity": equity,
                "free_collateral": free_collateral,
                "margin_used": margin_used,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Account Update - Equity: ${equity:.2f}, "
                f"Free Collateral: ${free_collateral:.2f}, "
                f"Margin Used: ${margin_used:.2f}"
            )

            # Call callback if registered
            if self.on_account_update:
                await self.on_account_update(account_data)

        except Exception as e:
            logger.error(f"Error handling subaccount update: {e}")

    async def handle_order_update(self, message: Dict[str, Any]) -> None:
        """Handle order status updates.

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

        Args:
            message: WebSocket message data
        """
        try:
            orders = message.get("contents", {}).get("orders", [])

            for order in orders:
                order_id = order.get("id")
                status = order.get("status")
                side = order.get("side")
                
                # Convert quantums to tokens
                size = int(order.get("quantums", 0)) / 1e6
                price = int(order.get("subticks", 0)) / 1e6

                order_data = {
                    "order_id": order_id,
                    "status": status,
                    "side": side,
                    "size": size,
                    "price": price,
                    "time_in_force": order.get("timeInForce"),
                    "reduce_only": order.get("reduceOnly"),
                    "post_only": order.get("postOnly"),
                    "updated_at": order.get("updatedAt"),
                    "timestamp": datetime.utcnow().isoformat(),
                }

                logger.info(
                    f"Order Update - ID: {order_id}, Status: {status}, "
                    f"Side: {side}, Size: {size}, Price: {price}"
                )

                # Call callback if registered
                if self.on_order_update:
                    await self.on_order_update(order_data)

        except Exception as e:
            logger.error(f"Error handling order update: {e}")

    async def handle_trade_update(self, message: Dict[str, Any]) -> None:
        """Handle trade fill updates.

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

        Args:
            message: WebSocket message data
        """
        try:
            trades = message.get("contents", {}).get("trades", [])

            for trade in trades:
                trade_id = trade.get("id")
                side = trade.get("side")
                
                # Convert quantums to tokens
                size = int(trade.get("size", 0)) / 1e6
                price = int(trade.get("price", 0)) / 1e6
                timestamp = trade.get("createdAt")

                trade_data = {
                    "trade_id": trade_id,
                    "side": side,
                    "size": size,
                    "price": price,
                    "created_at": timestamp,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                logger.info(
                    f"Trade Fill - ID: {trade_id}, Side: {side}, "
                    f"Size: {size}, Price: {price}, Time: {timestamp}"
                )

                # Call callback if registered
                if self.on_trade_update:
                    await self.on_trade_update(trade_data)

        except Exception as e:
            logger.error(f"Error handling trade update: {e}")

    async def handle_candle_update(self, message: Dict[str, Any]) -> None:
        """Handle candlestick data updates.

        Args:
            message: WebSocket message data
        """
        try:
            candles = message.get("contents", {}).get("candles", [])
            
            for candle in candles:
                logger.debug(
                    f"Candle Update - Symbol: {candle.get('ticker')}, "
                    f"Open: {candle.get('open')}, High: {candle.get('high')}, "
                    f"Low: {candle.get('low')}, Close: {candle.get('close')}"
                )

        except Exception as e:
            logger.error(f"Error handling candle update: {e}")

    async def handle_orderbook_update(self, message: Dict[str, Any]) -> None:
        """Handle orderbook updates.

        Args:
            message: WebSocket message data
        """
        try:
            orderbook = message.get("contents", {}).get("orderbook", {})
            
            bids = orderbook.get("bids", [])
            asks = orderbook.get("asks", [])
            
            logger.debug(
                f"Orderbook Update - Bids: {len(bids)}, Asks: {len(asks)}"
            )

        except Exception as e:
            logger.error(f"Error handling orderbook update: {e}")


# Standalone handler functions for use with WebSocketManager

async def handle_subaccount_update(message: Dict[str, Any]) -> None:
    """Standalone handler for subaccount updates.

    Args:
        message: WebSocket message data
    """
    handlers = WebSocketHandlers()
    await handlers.handle_subaccount_update(message)


async def handle_order_update(message: Dict[str, Any]) -> None:
    """Standalone handler for order updates.

    Args:
        message: WebSocket message data
    """
    handlers = WebSocketHandlers()
    await handlers.handle_order_update(message)


async def handle_trade_update(message: Dict[str, Any]) -> None:
    """Standalone handler for trade updates.

    Args:
        message: WebSocket message data
    """
    handlers = WebSocketHandlers()
    await handlers.handle_trade_update(message)
