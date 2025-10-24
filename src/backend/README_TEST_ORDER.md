# dYdX Test Order Guide

This guide will help you place test orders on the dYdX testnet to verify your configuration.

## Prerequisites

1. **dYdX Testnet Account**: You need a dYdX testnet wallet with some test tokens
2. **Wallet Mnemonic**: Your 12 or 24-word seed phrase for the testnet wallet
3. **Test Tokens**: Get test tokens from the [dYdX Testnet Faucet](https://faucet.v4testnet.dydx.exchange)

## Environment Configuration

The `.env` file is already configured for testnet:
- Testnet RPC: `https://dydx-testnet-rpc.publicnode.com:443`
- Testnet Indexer: `https://indexer.v4testnet.dydx.exchange`
- Testnet WebSocket: `wss://indexer.v4testnet.dydx.exchange/v4/ws`

## Getting Test Tokens

1. Visit the [dYdX Testnet Faucet](https://faucet.v4testnet.dydx.exchange)
2. Connect your testnet wallet
3. Request test USDC tokens
4. Wait for the transaction to confirm

## Using the Test Order Script

### Basic Usage

```bash
cd dydx-trading-service/backend
python3 test_order.py --mnemonic "your twelve or twenty-four word seed phrase" --symbol BTC-USD --side buy --size 0.001
```

### Command Line Options

- `--mnemonic`: Your wallet mnemonic phrase (required)
- `--symbol`: Trading pair (default: BTC-USD)
- `--side`: Order side - buy or sell (default: buy)
- `--size`: Order size (default: 0.001)
- `--price`: Limit price (optional - will use market price if not provided)
- `--network`: Network ID (1=mainnet, 11155111=testnet, default: testnet)
- `--test-connection`: Only test connection, don't place order

### Examples

#### Test Connection Only
```bash
python3 test_order.py --mnemonic "your mnemonic here" --test-connection
```

#### Place a Small Buy Order
```bash
python3 test_order.py --mnemonic "your mnemonic here" --symbol ETH-USD --side buy --size 0.01
```

#### Place a Sell Order with Custom Price
```bash
python3 test_order.py --mnemonic "your mnemonic here" --symbol BTC-USD --side sell --size 0.001 --price 50000
```

## What the Script Does

1. **Connection Test**: Verifies that your dYdX client can connect to the testnet
2. **Account Check**: Retrieves your account information and balance
3. **Market Price**: Gets current market price for the trading pair
4. **Order Placement**: Places a limit order slightly above/below market price
5. **Order Confirmation**: Shows order details including order ID and status

## Troubleshooting

### Common Issues

1. **"Client creation failed"**: Check your mnemonic phrase is correct
2. **"Insufficient balance"**: Make sure you have test tokens from the faucet
3. **"Invalid symbol"**: Use dYdX format symbols (e.g., BTC-USD, ETH-USD)
4. **"Network error"**: Verify your internet connection and testnet URLs

### Getting Help

If you encounter issues:
1. Check the logs for detailed error messages
2. Verify your testnet wallet has funds
3. Ensure you're using the correct network (testnet, not mainnet)
4. Check that your mnemonic phrase is for the correct wallet

## Next Steps

After successfully placing a test order:
1. Monitor your order status using the dYdX testnet interface
2. Try different order types and parameters
3. Test your webhook integration with the test order
4. Once comfortable, you can switch to mainnet by updating the `.env` file

## Safety Notes

- This script only places test orders on the dYdX testnet
- Testnet tokens have no real value
- Always verify your configuration before using mainnet
- Keep your mnemonic phrases secure and never share them