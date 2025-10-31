# dYdX Official Documentation - Quick Reference

**Source**: https://docs.dydx.xyz/  
**Last Updated**: October 31, 2025

---

## Installation

```bash
# Option 1: Clone and install
git clone https://github.com/dydxprotocol/v4-clients.git
cd v4-clients/v4-client-py-v2
poetry install

# Option 2: PyPI
pip install dydx-v4-client
```

---

## Quick Setup

### Node Client (for trading)

```python
from dydx_v4_client.network import make_mainnet, make_testnet
from dydx_v4_client.node.client import NodeClient

# Testnet
config = make_testnet(
    node_url="https://oegs-testnet.dydx.exchange:443",
    rest_indexer="https://indexer.v4testnet.dydx.exchange",
    websocket_indexer="wss://indexer.v4testnet.dydx.exchange/v4/ws"
).node

# Mainnet
config = make_mainnet(
    node_url="https://oegs.dydx.trade:443",
    rest_indexer="https://indexer.dydx.trade",
    websocket_indexer="wss://indexer.dydx.trade/v4/ws"
).node

# Connect
node = await NodeClient.connect(config)
```

### Indexer Client (for data)

```python
from dydx_v4_client.indexer.rest.indexer_client import IndexerClient

indexer = IndexerClient("https://indexer.v4testnet.dydx.exchange")
```

### Wallet

```python
from dydx_v4_client.wallet import Wallet

wallet = await Wallet.from_mnemonic(node, mnemonic, address)
```

---

## Place an Order - Complete Example

```python
import random
from dydx_v4_client.node.market import Market
from dydx_v4_client import OrderFlags
from dydx_v4_client.indexer.rest.constants import OrderType

# 1. Get market data
markets = await indexer.markets.get_perpetual_markets("BTC-USD")
market = Market(markets["markets"]["BTC-USD"])

# 2. Create order ID
order_id = market.order_id(
    wallet.address,
    0,  # subaccount number
    random.randint(0, 100000000),  # client ID
    OrderFlags.SHORT_TERM
)

# 3. Get block height
good_til_block = await node.latest_block_height() + 10

# 4. Build order
order = market.order(
    order_id=order_id,
    order_type=OrderType.MARKET,  # or OrderType.LIMIT
    side=1,  # 1 = BUY, -1 = SELL
    size=0.01,
    price=0,  # 0 for market orders
    time_in_force=1,  # 1 = IOC (Immediate or Cancel)
    reduce_only=False,
    good_til_block=good_til_block,
)

# 5. Broadcast order
tx_result = await node.place_order(wallet, order)
tx_hash = tx_result.tx_response.txhash
```

---

## Indexer API - Common Endpoints

### Get Account Info

```python
# Get subaccount
subaccount = await indexer.accounts.get_subaccount(
    address="dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art",
    subaccount_number=0
)

# Returns: equity, freeCollateral, marginUsed, etc.
```

### Get Positions

```python
# Get perpetual positions
positions = await indexer.accounts.get_subaccount_perpetual_positions(
    address="dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art",
    subaccount_number=0,
    status="OPEN"  # or "CLOSED", "LIQUIDATED"
)
```

### Get Orders

```python
# Get orders for subaccount
orders = await indexer.accounts.get_subaccount_orders(
    address="dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art",
    subaccount_number=0,
    ticker="BTC-USD",
    status="OPEN"  # or "FILLED", "CANCELED"
)
```

### Get Market Data

```python
# Get all markets
markets = await indexer.markets.get_perpetual_markets()

# Get specific market
market = await indexer.markets.get_perpetual_markets("BTC-USD")

# Get orderbook
orderbook = await indexer.markets.get_perpetual_market_orderbook("BTC-USD")

# Get trades
trades = await indexer.markets.get_perpetual_market_trades("BTC-USD")

# Get candles
candles = await indexer.markets.get_perpetual_market_candles(
    "BTC-USD",
    resolution="1DAY"
)
```

---

## WebSocket - Real-time Updates

### Connect

```python
from dydx_v4_client.indexer.socket.websocket import IndexerSocket
import json

socket = await IndexerSocket("wss://indexer.v4testnet.dydx.exchange/v4/ws").connect()
```

### Subscribe to Channels

```python
# Account updates
await socket.subscribe(
    channel="v4_accounts",
    id="dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art"
)

# Order updates
await socket.subscribe(
    channel="v4_orders",
    id="dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art"
)

# Market updates
await socket.subscribe(
    channel="v4_markets",
    id="BTC-USD"
)

# Trade updates
await socket.subscribe(
    channel="v4_trades",
    id="BTC-USD"
)

# Block height updates
await socket.subscribe(
    channel="v4_blockheight"
)
```

### Listen for Messages

```python
async for message in socket:
    data = json.loads(message)
    print(data)
```

---

## Cancel an Order

```python
# Cancel order
tx_result = await node.cancel_order(
    wallet=wallet,
    order_id=order_id,
    good_til_block=good_til_block
)
```

---

## Order Parameters

### Order Type
- `OrderType.MARKET` - Execute immediately
- `OrderType.LIMIT` - Execute at price or better
- `OrderType.STOP` - Trigger at price
- `OrderType.TAKE_PROFIT` - Close at profit target

### Order Side
- `1` or `BUY` - Purchase
- `-1` or `SELL` - Sell

### Time in Force
- `0` - UNSPECIFIED (default)
- `1` - IOC (Immediate or Cancel)
- `2` - FOK (Fill or Kill)
- `3` - POST_ONLY

### Order Flags
- `OrderFlags.SHORT_TERM` (0) - Valid ~30 seconds
- `OrderFlags.LONG_TERM` (64) - Valid 95 days
- `OrderFlags.CONDITIONAL` (32) - Conditional order

---

## Endpoints Reference

### Testnet

| Service | URL |
|---------|-----|
| Node RPC | `https://oegs-testnet.dydx.exchange:443` |
| Indexer REST | `https://indexer.v4testnet.dydx.exchange` |
| Indexer WebSocket | `wss://indexer.v4testnet.dydx.exchange/v4/ws` |

### Mainnet

| Service | URL |
|---------|-----|
| Node RPC | `https://oegs.dydx.trade:443` |
| Indexer REST | `https://indexer.dydx.trade` |
| Indexer WebSocket | `wss://indexer.dydx.trade/v4/ws` |

---

## Common Patterns

### Pattern 1: Query Account Data

```python
# Get account equity and collateral
subaccount = await indexer.accounts.get_subaccount(address, 0)
equity = subaccount["subaccount"]["equity"]
free_collateral = subaccount["subaccount"]["freeCollateral"]
```

### Pattern 2: Get Current Positions

```python
# Get all open positions
positions = await indexer.accounts.get_subaccount_perpetual_positions(
    address, 0, status="OPEN"
)

for position in positions["positions"]:
    print(f"{position['market']}: {position['size']} {position['side']}")
```

### Pattern 3: Monitor Order Status

```python
# Get specific order
orders = await indexer.accounts.get_subaccount_orders(
    address, 0, ticker="BTC-USD"
)

for order in orders["orders"]:
    if order["id"] == order_id:
        print(f"Status: {order['status']}")
        print(f"Filled: {order['filledSize']}")
```

### Pattern 4: Real-time Account Updates

```python
# Subscribe to account updates
await socket.subscribe("v4_accounts", address)

# Listen for updates
async for message in socket:
    data = json.loads(message)
    if data["type"] == "channel_data":
        print(f"New equity: {data['contents']['subaccount']['equity']}")
```

---

## Error Handling

```python
try:
    tx_result = await node.place_order(wallet, order)
except Exception as e:
    print(f"Order failed: {e}")
    # Handle error
```

---

## Best Practices

1. **Always test on testnet first**
   ```python
   config = make_testnet(...)  # Use testnet
   ```

2. **Use short-term orders by default**
   ```python
   OrderFlags.SHORT_TERM  # ~30 seconds, lower fees
   ```

3. **Add buffer to good_til_block**
   ```python
   good_til_block = await node.latest_block_height() + 10
   ```

4. **Validate market exists before trading**
   ```python
   markets = await indexer.markets.get_perpetual_markets("BTC-USD")
   if "BTC-USD" not in markets["markets"]:
       raise ValueError("Market not found")
   ```

5. **Handle WebSocket reconnections**
   ```python
   max_retries = 5
   for attempt in range(max_retries):
       try:
           socket = await IndexerSocket(ws_url).connect()
           break
       except Exception as e:
           await asyncio.sleep(2 ** attempt)
   ```

6. **Use reduce_only for closing positions**
   ```python
   order = market.order(
       ...,
       reduce_only=True,  # Only close, don't reverse
   )
   ```

---

## Useful Links

- **Official Docs**: https://docs.dydx.xyz/
- **Python Quick Start**: https://docs.dydx.xyz/interaction/client/quick-start-py
- **Trading Guide**: https://docs.dydx.xyz/interaction/trading
- **Indexer API**: https://docs.dydx.xyz/indexer-client/http
- **Node Client**: https://docs.dydx.xyz/node-client
- **WebSocket API**: https://docs.dydx.xyz/indexer-client/websockets
- **GitHub**: https://github.com/dydxprotocol/v4-clients
- **Status Page**: https://grpc-status.dydx.trade/

---

## Testnet Faucet

Get test funds on testnet:

```python
from dydx_v4_client.network import TESTNET_FAUCET
from dydx_v4_client.faucet_client import FaucetClient

faucet = FaucetClient(TESTNET_FAUCET)
# Request funds for your address
```

---

**Last Updated**: October 31, 2025  
**dYdX API Version**: V4
