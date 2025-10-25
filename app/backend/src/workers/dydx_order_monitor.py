"""
dYdX Order Monitoring Module - Batch Order Status Checking.

This module provides efficient batch processing for checking dYdX order
status across multiple positions and users.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import time

from ..bot.dydx_client import DydxClient
from ..db.models import Position

logger = logging.getLogger(__name__)


class DydxOrderMonitor:
    """Handles batch dYdX order status checking with rate limiting and error handling."""

    def __init__(self, max_concurrent: int = 10, rate_limit_delay: float = 0.1):
        """Initialize the order monitor.

        Args:
            max_concurrent: Maximum concurrent dYdX API calls
            rate_limit_delay: Delay between API calls to respect rate limits
        """
        self.max_concurrent = max_concurrent
        self.rate_limit_delay = rate_limit_delay
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def check_order_status_batch(
        self,
        positions: List[Position],
        credentials: Dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        """Check status of multiple dYdX orders efficiently.

        Args:
            positions: List of positions to check
            credentials: User credentials for dYdX access

        Returns:
            Dictionary mapping position_id to order status data
        """
        if not positions:
            return {}

        logger.debug(f"Checking order status for {len(positions)} positions")

        # Create dYdX client
        try:
            dydx_client = await DydxClient.create_client(
                eth_private_key=credentials['dydx_private_key'],
                network_id=1  # Mainnet
            )
        except Exception as e:
            logger.error(f"Failed to create dYdX client: {e}")
            return {}

        # Collect all unique order IDs to check
        order_ids_to_check = set()

        for position in positions:
            if position.dydx_order_id:
                order_ids_to_check.add(position.dydx_order_id)
            if position.tp_order_id:
                order_ids_to_check.add(position.tp_order_id)
            if position.sl_order_id:
                order_ids_to_check.add(position.sl_order_id)

        if not order_ids_to_check:
            logger.debug("No order IDs to check")
            return {}

        logger.debug(f"Checking {len(order_ids_to_check)} unique order IDs")

        # Check orders in batches with rate limiting
        order_results = {}

        # Process in smaller batches to avoid overwhelming the API
        batch_size = min(20, len(order_ids_to_check))  # Reasonable batch size

        for i in range(0, len(order_ids_to_check), batch_size):
            batch_order_ids = list(order_ids_to_check)[i:i + batch_size]

            try:
                # Check this batch of orders
                batch_results = await self._check_order_batch(
                    dydx_client, batch_order_ids, credentials
                )

                # Merge results
                order_results.update(batch_results)

                # Rate limiting delay between batches
                if i + batch_size < len(order_ids_to_check):
                    await asyncio.sleep(self.rate_limit_delay)

            except Exception as e:
                logger.error(f"Error checking order batch {i//batch_size + 1}: {e}")
                continue

        # Map results back to positions
        position_order_data = {}

        for position in positions:
            position_key = str(position.id)
            position_data = {
                'position_id': position.id,
                'symbol': position.symbol,
                'orders': {}
            }

            # Check each order type for this position
            if position.dydx_order_id:
                order_id = position.dydx_order_id
                if order_id in order_results:
                    position_data['orders']['entry'] = order_results[order_id]
                else:
                    position_data['orders']['entry'] = {'status': 'NOT_FOUND', 'error': 'Order not found'}

            if position.tp_order_id:
                order_id = position.tp_order_id
                if order_id in order_results:
                    position_data['orders']['tp'] = order_results[order_id]
                else:
                    position_data['orders']['tp'] = {'status': 'NOT_FOUND', 'error': 'Order not found'}

            if position.sl_order_id:
                order_id = position.sl_order_id
                if order_id in order_results:
                    position_data['orders']['sl'] = order_results[order_id]
                else:
                    position_data['orders']['sl'] = {'status': 'NOT_FOUND', 'error': 'Order not found'}

            position_order_data[position_key] = position_data

        logger.debug(f"Completed order status check for {len(positions)} positions")
        return position_order_data

    async def _check_order_batch(
        self,
        dydx_client: DydxClient,
        order_ids: List[str],
        credentials: Dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        """Check status of a batch of orders concurrently."""
        async def check_single_order(order_id: str) -> Tuple[str, Dict[str, Any]]:
            """Check status of a single order with error handling."""
            async with self._semaphore:  # Respect concurrency limit
                try:
                    result = await DydxClient.get_order_status(dydx_client, order_id)

                    if result['success']:
                        return order_id, {
                            'status': result.get('status', 'UNKNOWN'),
                            'symbol': result.get('symbol'),
                            'side': result.get('side'),
                            'size': result.get('size'),
                            'price': result.get('price'),
                            'remaining_size': result.get('remaining_size'),
                            'created_at': result.get('created_at'),
                            'updated_at': result.get('updated_at'),
                            'error': None
                        }
                    else:
                        return order_id, {
                            'status': 'ERROR',
                            'error': result.get('error', 'Unknown error'),
                            'symbol': None,
                            'side': None,
                            'size': None,
                            'price': None,
                            'remaining_size': None,
                            'created_at': None,
                            'updated_at': None
                        }

                except Exception as e:
                    logger.error(f"Error checking order {order_id}: {e}")
                    return order_id, {
                        'status': 'ERROR',
                        'error': str(e),
                        'symbol': None,
                        'side': None,
                        'size': None,
                        'price': None,
                        'remaining_size': None,
                        'created_at': None,
                        'updated_at': None
                    }

        # Check all orders concurrently
        tasks = [check_single_order(order_id) for order_id in order_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        order_data = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed: {result}")
                continue

            order_id, data = result
            order_data[order_id] = data

        return order_data

    async def get_order_details(
        self,
        client: DydxClient,
        order_id: str
    ) -> Dict[str, Any]:
        """Get detailed order information from dYdX."""
        try:
            result = await DydxClient.get_order_status(client, order_id)

            if result['success']:
                return {
                    'order_id': order_id,
                    'status': result.get('status'),
                    'symbol': result.get('symbol'),
                    'side': result.get('side'),
                    'type': result.get('type'),
                    'size': result.get('size'),
                    'price': result.get('price'),
                    'remaining_size': result.get('remaining_size'),
                    'created_at': result.get('created_at'),
                    'updated_at': result.get('updated_at'),
                    'filled_at': None,  # Would need additional API call to get this
                }
            else:
                return {
                    'order_id': order_id,
                    'status': 'ERROR',
                    'error': result.get('error'),
                }

        except Exception as e:
            logger.error(f"Failed to get order details for {order_id}: {e}")
            return {
                'order_id': order_id,
                'status': 'ERROR',
                'error': str(e),
            }

    async def cancel_order_if_exists(
        self,
        client: DydxClient,
        order_id: str
    ) -> bool:
        """Safely cancel order with existence check."""
        try:
            if not order_id:
                return False

            # First check if order exists and is cancellable
            order_details = await self.get_order_details(client, order_id)

            if order_details.get('status') == 'ERROR':
                logger.warning(f"Order {order_id} not found or already cancelled")
                return False

            # Check if order is in cancellable state
            status = order_details.get('status', '').upper()
            if status in ['FILLED', 'CANCELLED']:
                logger.info(f"Order {order_id} is {status}, no need to cancel")
                return True

            # Cancel the order
            cancel_result = await DydxClient.cancel_order(client, order_id)

            if cancel_result:
                logger.info(f"Successfully cancelled order {order_id}")
                return True
            else:
                logger.error(f"Failed to cancel order {order_id}")
                return False

        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    async def validate_order_ownership(
        self,
        order_id: str,
        expected_symbol: str,
        credentials: Dict[str, str]
    ) -> bool:
        """Verify order belongs to expected position."""
        try:
            # Create dYdX client
            dydx_client = await DydxClient.create_client(
                mnemonic=credentials['dydx_mnemonic'],
                network_id=1
            )

            # Get order details
            order_details = await self.get_order_details(dydx_client, order_id)

            if order_details.get('status') == 'ERROR':
                logger.warning(f"Cannot validate ownership for order {order_id}: {order_details.get('error')}")
                return False

            # Check if symbol matches
            actual_symbol = order_details.get('symbol')
            if actual_symbol != expected_symbol:
                logger.warning(
                    f"Order {order_id} symbol mismatch: expected {expected_symbol}, got {actual_symbol}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating order ownership for {order_id}: {e}")
            return False

    async def get_account_positions_batch(
        self,
        credentials_list: List[Dict[str, str]]
    ) -> Dict[str, Dict[str, Any]]:
        """Get positions for multiple accounts efficiently."""
        async def get_single_account_positions(credentials: Dict[str, str]) -> Tuple[str, Dict[str, Any]]:
            """Get positions for a single account."""
            try:
                dydx_client = await DydxClient.create_client(
                    mnemonic=credentials['dydx_mnemonic'],
                    network_id=1
                )

                account_info = await DydxClient.get_account_info(dydx_client)

                if account_info['success']:
                    return credentials['wallet_address'], {
                        'success': True,
                        'positions': account_info.get('positions', []),
                        'account': account_info.get('account', {}),
                    }
                else:
                    return credentials['wallet_address'], {
                        'success': False,
                        'error': account_info.get('error'),
                        'positions': [],
                    }

            except Exception as e:
                logger.error(f"Error getting account positions for {credentials.get('wallet_address')}: {e}")
                return credentials['wallet_address'], {
                    'success': False,
                    'error': str(e),
                    'positions': [],
                }

        # Process all accounts concurrently
        tasks = [get_single_account_positions(creds) for creds in credentials_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        account_positions = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Account position task failed: {result}")
                continue

            wallet_address, data = result
            account_positions[wallet_address] = data

        return account_positions

    async def get_market_data_batch(
        self,
        symbols: List[str],
        credentials: Dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        """Get market data for multiple symbols efficiently."""
        try:
            # Create dYdX client
            dydx_client = await DydxClient.create_client(
                mnemonic=credentials['dydx_mnemonic'],
                network_id=1
            )

            # Get all market data in one call
            markets_result = await DydxClient.get_account_info(dydx_client)  # This doesn't actually get markets

            # For now, we'll get market data one by one (dYdX API structure may vary)
            market_data = {}

            for symbol in symbols:
                try:
                    price_result = await DydxClient.get_market_price(dydx_client, symbol)

                    if price_result['success']:
                        market_data[symbol] = {
                            'symbol': symbol,
                            'price': price_result.get('price'),
                            'index_price': price_result.get('index_price'),
                            'mark_price': price_result.get('mark_price'),
                        }
                    else:
                        market_data[symbol] = {
                            'symbol': symbol,
                            'error': price_result.get('error'),
                        }

                    # Rate limiting
                    await asyncio.sleep(self.rate_limit_delay)

                except Exception as e:
                    logger.error(f"Error getting market data for {symbol}: {e}")
                    market_data[symbol] = {
                        'symbol': symbol,
                        'error': str(e),
                    }

            return market_data

        except Exception as e:
            logger.error(f"Error in batch market data request: {e}")
            return {symbol: {'symbol': symbol, 'error': str(e)} for symbol in symbols}