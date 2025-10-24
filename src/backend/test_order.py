#!/usr/bin/env python3
"""
dYdX Test Order Script

This script allows you to place test orders on the dYdX testnet to verify
that your configuration is working correctly.

Usage:
    python test_order.py --mnemonic "your mnemonic phrase here" --symbol BTC-USD --side buy --size 0.001
"""

import argparse
import asyncio
import logging
import sys
from decimal import Decimal

# Add the src directory to the path so we can import our modules
sys.path.append('src')

from bot.dydx_client import DydxClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_dydx_connection(mnemonic: str, network_id: int = 11155111) -> bool:
    """Test basic dYdX connection."""
    try:
        logger.info(f"Creating dYdX client for network {network_id}...")
        client = await DydxClient.create_client(mnemonic, network_id)

        logger.info("Testing connection by getting last block...")
        last_block = await client.node_client.get_last_block()
        logger.info(f"Successfully connected! Last block: {last_block.get('blockHeight', 'unknown')}")

        logger.info("Testing account info retrieval...")
        account_info = await DydxClient.get_account_info(client)
        if account_info['success']:
            logger.info("Account info retrieved successfully")
            logger.info(f"Account address: {account_info['account']['address']}")
            logger.info(f"Free collateral: {account_info['account']['free_collateral']}")
        else:
            logger.warning(f"Could not retrieve account info: {account_info['error']}")

        return True

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False


async def place_test_order(
    mnemonic: str,
    symbol: str,
    side: str,
    size: str,
    price: str = None,
    network_id: int = 11155111
) -> bool:
    """Place a test order on dYdX."""
    try:
        logger.info(f"Creating dYdX client for trading on network {network_id}...")
        client = await DydxClient.create_client(mnemonic, network_id)

        # Get current market price for reference
        if price is None:
            logger.info(f"Getting market price for {symbol}...")
            price_info = await DydxClient.get_market_price(client, symbol)
            if price_info['success']:
                current_price = float(price_info['price'])
                logger.info(f"Current market price for {symbol}: {current_price}")

                # For buy orders, set price slightly above market
                # For sell orders, set price slightly below market
                if side.upper() == 'BUY':
                    price = str(current_price * 1.001)  # 0.1% above market
                else:
                    price = str(current_price * 0.999)  # 0.1% below market

                logger.info(f"Using limit price: {price}")
            else:
                logger.warning(f"Could not get market price, using market order")
                order_type = 'MARKET'
            order_type = 'LIMIT'
        else:
            order_type = 'LIMIT'

        # Place the order
        if order_type == 'LIMIT':
            logger.info(f"Placing {order_type} order: {symbol} {side} {size} @ {price}")
            result = await DydxClient.place_limit_order(
                client, symbol, side, size, price, "GTT"
            )
        else:
            logger.info(f"Placing {order_type} order: {symbol} {side} {size}")
            result = await DydxClient.place_market_order(
                client, symbol, side, size
            )

        if result['success']:
            logger.info("✅ Order placed successfully!")
            logger.info(f"Order ID: {result['order_id']}")
            logger.info(f"Symbol: {result['symbol']}")
            logger.info(f"Side: {result['side']}")
            logger.info(f"Size: {result['size']}")
            logger.info(f"Type: {result['type']}")
            if 'price' in result:
                logger.info(f"Price: {result['price']}")
            logger.info(f"Status: {result['status']}")
            logger.info(f"Timestamp: {result['timestamp']}")
        else:
            logger.error(f"❌ Failed to place order: {result['error']}")
            return False

        return True

    except Exception as e:
        logger.error(f"Order placement failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Place a test order on dYdX testnet')
    parser.add_argument('--mnemonic', required=True, help='Your dYdX wallet mnemonic phrase')
    parser.add_argument('--symbol', default='BTC-USD', help='Trading pair symbol (default: BTC-USD)')
    parser.add_argument('--side', choices=['buy', 'sell'], default='buy', help='Order side (default: buy)')
    parser.add_argument('--size', default='0.001', help='Order size (default: 0.001)')
    parser.add_argument('--price', help='Limit price (optional, will use market price if not provided)')
    parser.add_argument('--network', type=int, default=11155111, help='Network ID (1=mainnet, 11155111=testnet, default: testnet)')
    parser.add_argument('--test-connection', action='store_true', help='Only test connection, don\'t place order')

    args = parser.parse_args()

    async def run_test():
        # First test the connection
        logger.info("🔧 Testing dYdX connection...")
        connection_ok = await test_dydx_connection(args.mnemonic, args.network)

        if not connection_ok:
            logger.error("❌ Connection test failed. Please check your mnemonic and network configuration.")
            return False

        if args.test_connection:
            logger.info("✅ Connection test passed! Use --no-test-connection to place an actual order.")
            return True

        # Place the test order
        logger.info("📈 Placing test order...")
        order_ok = await place_test_order(
            args.mnemonic, args.symbol, args.side, args.size, args.price, args.network
        )

        if order_ok:
            logger.info("✅ Test order completed successfully!")
            return True
        else:
            logger.error("❌ Test order failed.")
            return False

    # Run the async test
    success = asyncio.run(run_test())
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()