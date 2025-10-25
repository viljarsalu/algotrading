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
from dydx_v4_client.node.market import Market
from dydx_v4_client.network import make_mainnet, make_testnet
from dydx_v4_client.wallet import Wallet
from dydx_v4_client.key_pair import KeyPair
from src.core.config import get_settings
 
logger = logging.getLogger(__name__)
 
 
class DydxClient:
    """Stateless dYdX client for per-user trading operations."""

    # Default network configurations
    NETWORKS = {
        1: "mainnet",
        11155111: "testnet",  # Sepolia testnet
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
        mnemonic: Optional[str] = None,
    ) -> "DydxClient":
        """Create authenticated dYdX client instance.
        
        Uses provided mnemonic for user-specific context or falls back to
        the environment settings for system-level operations.

        Args:
            network_id: Optional network ID. Defaults to testnet if not in production.
            mnemonic: Optional dYdX mnemonic phrase (24 words) for user authentication.
        
        Returns:
            Authenticated DydxClient instance

        Raises:
            ValueError: If credentials are invalid or network is unsupported
        """
        try:
            settings = get_settings()
            
            # For multi-user support, mnemonic MUST be provided per-user
            # Do NOT fallback to environment variables for user trading
            if not mnemonic:
                raise ValueError(
                    "Mnemonic is required for trading operations. "
                    "Please configure your dYdX mnemonic in the dashboard."
                )
            
            user_mnemonic = mnemonic
            
            # Normalize mnemonic: strip whitespace, convert to lowercase, replace multiple spaces with single space
            user_mnemonic = ' '.join(user_mnemonic.strip().lower().split())
            
            # Validate mnemonic word count
            mnemonic_words = user_mnemonic.split()
            valid_word_counts = [12, 15, 18, 21, 24]
            if len(mnemonic_words) not in valid_word_counts:
                raise ValueError(f"Mnemonic must contain 12, 15, 18, 21, or 24 words. Got {len(mnemonic_words)} words: {user_mnemonic[:50]}...")

            # Default to testnet if not in production
            if network_id is None:
                network_id = 1 if settings.is_production() else 11155111

            # Validate network
            if network_id not in DydxClient.NETWORKS:
                raise ValueError(f"Unsupported network ID: {network_id}")
            
            network_type = DydxClient.NETWORKS[network_id]

            # Create network configuration based on network type
            if network_type == "mainnet":
                # Try primary endpoint first, with fallback options
                try:
                    config = make_mainnet(
                        node_url="https://dydx-ops-rpc.kingnodes.com",
                        rest_indexer="https://indexer.dydx.trade",
                        websocket_indexer="wss://indexer.dydx.trade/v4/ws"
                    ).node
                except Exception as e:
                    logger.warning(f"Primary mainnet RPC failed, trying fallback: {e}")
                    config = make_mainnet(
                        node_url="https://dydx-mainnet-rpc.allthatnode.com:1317",
                        rest_indexer="https://indexer.dydx.trade",
                        websocket_indexer="wss://indexer.dydx.trade/v4/ws"
                    ).node
            else:  # testnet
                # Use official dYdX testnet endpoints from docs.dydx.xyz
                testnet_endpoints = [
                    {
                        "node_url": "https://oegs-testnet.dydx.exchange:443",
                        "rest_indexer": "https://indexer.v4testnet.dydx.exchange",
                        "websocket_indexer": "wss://indexer.v4testnet.dydx.exchange/v4/ws"
                    },
                    {
                        "node_url": "https://testnet-dydx-rpc.lavenderfive.com",
                        "rest_indexer": "https://indexer.v4testnet.dydx.exchange",
                        "websocket_indexer": "wss://indexer.v4testnet.dydx.exchange/v4/ws"
                    },
                    {
                        "node_url": "https://test-dydx-rpc.kingnodes.com",
                        "rest_indexer": "https://indexer.v4testnet.dydx.exchange",
                        "websocket_indexer": "wss://indexer.v4testnet.dydx.exchange/v4/ws"
                    },
                    {
                        "node_url": "https://dydx-testnet-rpc.polkachu.com",
                        "rest_indexer": "https://indexer.v4testnet.dydx.exchange",
                        "websocket_indexer": "wss://indexer.v4testnet.dydx.exchange/v4/ws"
                    },
                    {
                        "node_url": "https://dydx-rpc-testnet.enigma-validator.com",
                        "rest_indexer": "https://indexer.v4testnet.dydx.exchange",
                        "websocket_indexer": "wss://indexer.v4testnet.dydx.exchange/v4/ws"
                    }
                ]
                
                config = None
                for endpoint in testnet_endpoints:
                    try:
                        config = make_testnet(
                            node_url=endpoint["node_url"],
                            rest_indexer=endpoint["rest_indexer"],
                            websocket_indexer=endpoint["websocket_indexer"]
                        ).node
                        logger.info(f"Using testnet endpoint: {endpoint['node_url']}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to configure testnet endpoint {endpoint['node_url']}: {e}")
                        continue
                
                if config is None:
                    raise ValueError("Failed to configure testnet endpoints")
            
            # Connect to the network using NodeClient.connect()
            node_client = await NodeClient.connect(config)
            
            # Create wallet from mnemonic for signing transactions
            try:
                # Step 1: Derive address from mnemonic
                # Create a temporary wallet to get the address
                key_pair = KeyPair.from_mnemonic(user_mnemonic)
                temp_wallet = Wallet(key_pair, 0, 0)
                address = temp_wallet.address  # address is a property, not a method
                
                logger.info(f"Derived address from mnemonic: {address}")
                
                # Step 2: Create the actual wallet for signing transactions
                wallet = await Wallet.from_mnemonic(node_client, user_mnemonic, address)
                
                # Store wallet in the client for later use
                node_client._wallet = wallet
                
                logger.info(f"Wallet created successfully from mnemonic")
            except Exception as e:
                logger.error(f"Failed to create wallet from mnemonic: {e}")
                raise ValueError(f"Wallet creation failed: {str(e)}")

            # Test connection
            await node_client.latest_block_height()

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

            # Place market order on dYdX V4
            try:
                # Get market info to convert symbol to market_id
                markets = await client.node_client.get_markets()
                market = None
                for m in markets:
                    if m.ticker == symbol:
                        market = m
                        break
                
                if not market:
                    raise ValueError(f"Market not found for symbol: {symbol}")
                
                market_id = market.id
                
                # Convert size to quantums (smallest unit)
                # For most assets, 1 quantum = 10^-8 of the asset
                size_quantums = int(float(size) * 10**8)
                
                # Place order using node client
                # Market orders use subticks = 0
                order_result = await client.node_client.place_order(
                    market_id=market_id,
                    side=1 if side.upper() == 'BUY' else -1,  # 1 for BUY, -1 for SELL
                    quantums=size_quantums,
                    subticks=0,  # 0 for market order
                    time_in_force=0,  # 0 for IOC (Immediate or Cancel)
                    reduce_only=False,
                    post_only=False,
                    client_metadata=0
                )
                
                logger.info(f"Market order placed successfully for {symbol}: {order_result}")
                
                return {
                    'success': True,
                    'order_id': str(order_result.get('order_id', 'unknown')),
                    'symbol': symbol,
                    'side': side.upper(),
                    'size': size,
                    'price': '0',
                    'type': 'MARKET',
                    'status': 'PENDING',
                    'tx_hash': order_result.get('tx_hash')
                }
                
            except Exception as e:
                logger.error(f"Failed to place market order on dYdX: {e}")
                raise

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

            # Place limit order on dYdX V4
            try:
                # Get market info to convert symbol to market_id
                markets = await client.node_client.get_markets()
                market = None
                for m in markets:
                    if m.ticker == symbol:
                        market = m
                        break
                
                if not market:
                    raise ValueError(f"Market not found for symbol: {symbol}")
                
                market_id = market.id
                
                # Convert size to quantums
                size_quantums = int(float(size) * 10**8)
                
                # Convert price to subticks
                # subticks = price * 10^8 / (10^-8) = price * 10^16
                # But we need to account for the atomic unit of the quote asset
                price_subticks = int(float(price) * 10**8)
                
                # Map time_in_force to dYdX values
                tif_map = {
                    'GTT': 0,  # Good-til-time
                    'IOC': 1,  # Immediate or Cancel
                    'FOK': 2,  # Fill or Kill
                }
                tif_value = tif_map.get(time_in_force, 0)
                
                # Place order using node client
                order_result = await client.node_client.place_order(
                    market_id=market_id,
                    side=1 if side.upper() == 'BUY' else -1,  # 1 for BUY, -1 for SELL
                    quantums=size_quantums,
                    subticks=price_subticks,
                    time_in_force=tif_value,
                    reduce_only=False,
                    post_only=False,
                    client_metadata=0
                )
                
                logger.info(f"Limit order placed successfully for {symbol}: {order_result}")
                
                return {
                    'success': True,
                    'order_id': str(order_result.get('order_id', 'unknown')),
                    'symbol': symbol,
                    'side': side.upper(),
                    'size': size,
                    'price': price,
                    'type': 'LIMIT',
                    'time_in_force': time_in_force,
                    'status': 'PENDING',
                    'tx_hash': order_result.get('tx_hash')
                }
                
            except Exception as e:
                logger.error(f"Failed to place limit order on dYdX: {e}")
                raise

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