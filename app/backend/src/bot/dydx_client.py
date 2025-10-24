"""
dYdX Client Module - Stateless dYdX Protocol Integration.

This module provides a stateless interface to the dYdX protocol v4,
accepting user credentials as parameters for each operation.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from dydx_v4_client.node.client import NodeClient
from dydx_v4_client.network import mainnet_node, testnet_node
from eth_account import Account
from src.core.config import get_settings
 
logger = logging.getLogger(__name__)
 
 
class DydxClient:
    """Stateless dYdX client for per-user trading operations."""

    # Default network configurations
    NETWORKS = {
        1: mainnet_node,
        11155111: testnet_node,  # Sepolia testnet
    }

    def __init__(self, node_client: NodeClient):
        """Initialize with authenticated dYdX node client.

        Args:
            node_client: Authenticated dYdX node client instance
        """
        self.node_client = node_client

    @staticmethod
    async def create_client(
        network_id: Optional[int] = None,
        eth_private_key: Optional[str] = None,
    ) -> "DydxClient":
        """Create authenticated dYdX client instance.
        
        Uses provided private key for user-specific context or falls back to
        the environment settings for system-level operations.

        Args:
            network_id: Optional network ID. Defaults to testnet if not in production.
            eth_private_key: Optional Ethereum private key for user authentication.
        
        Returns:
            Authenticated DydxClient instance

        Raises:
            ValueError: If credentials are invalid or network is unsupported
        """
        try:
            settings = get_settings()
            
            # Use provided key or fallback to environment settings
            private_key = eth_private_key or settings.dydx_v4.private_key

            if not private_key:
                raise ValueError("Ethereum private key is not provided and DYDX_V4_PRIVATE_KEY is not set.")

            # Default to testnet if not in production
            if network_id is None:
                network_id = 1 if settings.is_production() else 11155111

            # Validate network
            if network_id not in DydxClient.NETWORKS:
                raise ValueError(f"Unsupported network ID: {network_id}")
            
            network_config = DydxClient.NETWORKS[network_id]

            # Create account from private key
            account = Account.from_key(private_key)

            # Create dYdX node client
            from dydx_v4_client.chain.async_client import AsyncChainClient
            from dydx_v4_client.indexer.async_client import AsyncIndexerClient

            network_config_obj = network_config(channel="api")
            indexer_client = AsyncIndexerClient(network_config_obj)
            chain_client = AsyncChainClient(network_config_obj)
            
            node_client = NodeClient(
                indexer_client=indexer_client,
                chain_client=chain_client,
                eth_private_key=account.key.hex(),
            )

            # Test connection
            await node_client.get_last_block()

            logger.info(f"dYdX client created for network {network_id}")
            return DydxClient(node_client)

        except Exception as e:
            logger.error(f"Failed to create dYdX client: {e}")
            raise ValueError(f"Client creation failed: {str(e)}")

    @staticmethod
    async def place_market_order(
        client: "DydxClient",
        symbol: str,
        side: str,
        size: str,
        price: Optional[str] = None
    ) -> Dict[str, Any]:
        """Place market order with user-specific client.

        Args:
            client: Authenticated DydxClient instance
            symbol: Trading pair symbol (e.g., 'BTC-USD')
            side: Order side ('BUY' or 'SELL')
            size: Order size as string
            price: Optional price for limit orders (ignored for market orders)

        Returns:
            Order placement result with order details

        Raises:
            ValueError: If order parameters are invalid
        """
        try:
            # Validate order parameters
            if side.upper() not in ['BUY', 'SELL']:
                raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")

            if not size or float(size) <= 0:
                raise ValueError(f"Invalid size: {size}")

            # Create market order
            order_params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': 'MARKET',
                'size': size,
                'time_in_force': 'IOC',  # Immediate or Cancel
            }

            # Place the order
            order_result = await client.node_client.place_order(**order_params)

            logger.info(f"Market order placed: {symbol} {side} {size}")

            return {
                'success': True,
                'order_id': order_result.get('orderId'),
                'symbol': symbol,
                'side': side.upper(),
                'size': size,
                'type': 'MARKET',
                'status': order_result.get('status', 'PENDING'),
                'timestamp': order_result.get('createdAt'),
            }

        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol,
                'side': side,
                'size': size,
            }

    @staticmethod
    async def place_limit_order(
        client: "DydxClient",
        symbol: str,
        side: str,
        size: str,
        price: str,
        time_in_force: str = "GTT"
    ) -> Dict[str, Any]:
        """Place limit order with user-specific client.

        Args:
            client: Authenticated DydxClient instance
            symbol: Trading pair symbol (e.g., 'BTC-USD')
            side: Order side ('BUY' or 'SELL')
            size: Order size as string
            price: Limit price as string
            time_in_force: Time in force policy ('GTT', 'IOC', 'FOK')

        Returns:
            Order placement result with order details

        Raises:
            ValueError: If order parameters are invalid
        """
        try:
            # Validate order parameters
            if side.upper() not in ['BUY', 'SELL']:
                raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")

            if not size or float(size) <= 0:
                raise ValueError(f"Invalid size: {size}")

            if not price or float(price) <= 0:
                raise ValueError(f"Invalid price: {price}")

            if time_in_force not in ['GTT', 'IOC', 'FOK']:
                raise ValueError(f"Invalid time_in_force: {time_in_force}")

            # Create limit order
            order_params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': 'LIMIT',
                'size': size,
                'price': price,
                'time_in_force': time_in_force,
            }

            # Place the order
            order_result = await client.node_client.place_order(**order_params)

            logger.info(f"Limit order placed: {symbol} {side} {size} @ {price}")

            return {
                'success': True,
                'order_id': order_result.get('orderId'),
                'symbol': symbol,
                'side': side.upper(),
                'size': size,
                'price': price,
                'type': 'LIMIT',
                'time_in_force': time_in_force,
                'status': order_result.get('status', 'PENDING'),
                'timestamp': order_result.get('createdAt'),
            }

        except Exception as e:
            logger.error(f"Failed to place limit order: {e}")
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol,
                'side': side,
                'size': size,
                'price': price,
            }

    @staticmethod
    async def cancel_order(client: "DydxClient", order_id: str) -> bool:
        """Cancel existing order.

        Args:
            client: Authenticated DydxClient instance
            order_id: dYdX order ID to cancel

        Returns:
            True if cancellation was successful

        Raises:
            ValueError: If order_id is invalid
        """
        try:
            if not order_id:
                raise ValueError("Order ID is required")

            # Cancel the order
            cancel_result = await client.node_client.cancel_order(order_id)

            logger.info(f"Order cancelled: {order_id}")

            return cancel_result.get('success', False)

        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    @staticmethod
    async def get_order_status(client: "DydxClient", order_id: str) -> Dict[str, Any]:
        """Retrieve order status and details.

        Args:
            client: Authenticated DydxClient instance
            order_id: dYdX order ID to query

        Returns:
            Order status and details

        Raises:
            ValueError: If order_id is invalid
        """
        try:
            if not order_id:
                raise ValueError("Order ID is required")

            # Get order status
            order_info = await client.node_client.get_order(order_id)

            return {
                'success': True,
                'order_id': order_id,
                'status': order_info.get('status'),
                'symbol': order_info.get('symbol'),
                'side': order_info.get('side'),
                'size': order_info.get('size'),
                'price': order_info.get('price'),
                'type': order_info.get('type'),
                'remaining_size': order_info.get('remainingSize'),
                'created_at': order_info.get('createdAt'),
                'updated_at': order_info.get('updatedAt'),
            }

        except Exception as e:
            logger.error(f"Failed to get order status for {order_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'order_id': order_id,
            }

    @staticmethod
    async def get_account_info(client: "DydxClient") -> Dict[str, Any]:
        """Get account balances and positions.

        Args:
            client: Authenticated DydxClient instance

        Returns:
            Account information including balances and positions
        """
        try:
            # Get account information
            account_info = await client.node_client.get_account()

            # Get positions
            positions = await client.node_client.get_positions()

            # Get subaccount information
            subaccount_info = await client.node_client.get_subaccount()

            return {
                'success': True,
                'account': {
                    'address': account_info.get('address'),
                    'equity': account_info.get('equity'),
                    'free_collateral': account_info.get('freeCollateral'),
                    'pending_deposits': account_info.get('pendingDeposits'),
                    'pending_withdrawals': account_info.get('pendingWithdrawals'),
                    'open_notional': account_info.get('openNotional'),
                    'notional_total': account_info.get('notionalTotal'),
                },
                'positions': positions.get('positions', []),
                'subaccount': {
                    'address': subaccount_info.get('address'),
                    'equity': subaccount_info.get('equity'),
                    'free_collateral': subaccount_info.get('freeCollateral'),
                    'margin_used': subaccount_info.get('marginUsed'),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return {
                'success': False,
                'error': str(e),
            }

    @staticmethod
    async def get_market_price(client: "DydxClient", symbol: str) -> Dict[str, Any]:
        """Get current market price for a symbol.

        Args:
            client: Authenticated DydxClient instance
            symbol: Trading pair symbol

        Returns:
            Current market price information
        """
        try:
            # Get market data
            markets = await client.node_client.get_markets()

            if symbol not in markets.get('markets', {}):
                return {
                    'success': False,
                    'error': f"Symbol {symbol} not found",
                }

            market_data = markets['markets'][symbol]

            return {
                'success': True,
                'symbol': symbol,
                'price': market_data.get('oraclePrice'),
                'index_price': market_data.get('indexPrice'),
                'mark_price': market_data.get('markPrice'),
                'next_funding_rate': market_data.get('nextFundingRate'),
                'next_funding_time': market_data.get('nextFundingTime'),
            }

        except Exception as e:
            logger.error(f"Failed to get market price for {symbol}: {e}")
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol,
            }