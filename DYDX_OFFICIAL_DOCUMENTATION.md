# Official dYdX Documentation Summary

**Source**: https://docs.dydx.xyz/  
**Last Updated**: October 31, 2025  
**Version**: dYdX V4

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Available Clients](#available-clients)
4. [Endpoints](#endpoints)
5. [Trading Guide](#trading-guide)
6. [Indexer API](#indexer-api)
7. [Node Client API](#node-client-api)
8. [WebSocket API](#websocket-api)

---

## Overview

dYdX Integration Documentation is crafted specifically for developers who want to build:
- Trading applications
- Trading bots
- Analytics tools
- Integrated platforms

The documentation provides everything needed:
- REST & WebSocket API references
- Integration guides
- High-frequency trading bot support
- DeFi dashboard building

---

## Getting Started

### Installation

**Python 3.9+** and **Poetry** required

```bash
# Clone the dydx client repo
git clone https://github.com/dydxprotocol/v4-clients.git

# Navigate to Python client
cd v4-clients/v4-client-py-v2

# Install dependencies
poetry install
```

**Or via PyPI**:
```bash
pip install dydx-v4-client
```

### Run Examples

```bash
poetry run python -m examples.account_endpoints
```

---

## Available Clients

### 1. Node Client (Validator Client)

**Purpose**: Main client for interacting with dYdX network

**Features**:
- Provides Node API for authenticated operations
- Private API for trading orders
- Requires RPC/gRPC endpoint
- Requires HTTP and WebSocket endpoints (Python)

**Setup**:
```python
from dydx_v4_client.network import make_mainnet
from dydx_v4_client.node.client import NodeClient

config = make_mainnet(
    node_url="oegs.dydx.trade:443",
    rest_indexer="https://indexer.dydx.trade",
    websocket_indexer="wss://indexer.dydx.trade/v4/ws",
).node

# Connect to the network
node = await NodeClient.connect(config)
```

---

### 2. Indexer Client

**Purpose**: High-availability system for structured data

**Features**:
- REST API for spontaneous data retrieval
- WebSocket API for continuous data streaming
- Public API (no authentication required)
- Preferred for data queries

**Setup**:
```python
from dydx_v4_client.network import make_mainnet
from dydx_v4_client.indexer.rest.indexer_client import IndexerClient
from dydx_v4_client.indexer.socket.websocket import IndexerSocket

config = make_mainnet(
    node_url="your-custom-grpc-node.com",
    rest_indexer="https://your-custom-rest-indexer.com",
    websocket_indexer="wss://your-custom-websocket-indexer.com"
).node

# HTTP sub-client
indexer = IndexerClient(config.rest_indexer)

# WebSocket sub-client
socket = await IndexerSocket(config.websocket_indexer).connect()
```

---

### 3. Composite Client (TypeScript only)

Groups commonly used methods into a single structure.

```typescript
import { CompositeClient, Network } from '@dydxprotocol/v4-client-js';

const network = Network.mainnet();
const client = await CompositeClient.connect(network);
```

---

### 4. Faucet Client

**Purpose**: Request test funds on testnet

**Note**: Only works on testnet. Test funds can only be used on testnet.

```python
from dydx_v4_client.network import TESTNET_FAUCET
from dydx_v4_client.faucet_client import FaucetClient

faucet = FaucetClient(TESTNET_FAUCET)
```

---

## Endpoints

### Node Endpoints

**Testnet**:
- gRPC: `oegs-testnet.dydx.exchange:443`
- HTTP: `https://testnet-lcd.dydx.exchange`
- WebSocket: `wss://testnet-lcd.dydx.exchange/websocket`

**Mainnet**:
- gRPC: `oegs.dydx.trade:443`
- HTTP: `https://dydx-mainnet-lcd.allthatnode.com:1317`
- WebSocket: `wss://dydx-mainnet-lcd.allthatnode.com:1317/websocket`

**Status Check**: https://grpc-status.dydx.trade/

---

### Indexer Endpoints

**Testnet**:
- REST: `https://indexer.v4testnet.dydx.exchange`
- WebSocket: `wss://indexer.v4testnet.dydx.exchange/v4/ws`

**Mainnet**:
- REST: `https://indexer.dydx.trade`
- WebSocket: `wss://indexer.dydx.trade/v4/ws`

---

## Trading Guide

### Place an Order

#### Step 1: Get Market Parameters

Fetch market data from the indexer:

```python
# Query market data
markets = await indexer.markets.get_perpetual_markets(market_id)
market = Market(markets["markets"][market_id])
```

---

#### Step 2: Identify the Order

Every order has a unique identifier composed of:

- **Subaccount ID**: Account address + subaccount integer
- **Client ID**: 32-bit integer chosen by user (unique per subaccount)
- **Order Flags**: 
  - `0` = Short-term order
  - `64` = Long-term order
  - `32` = Conditional order
- **CLOB Pair ID**: ID of underlying market/perpetual

```python
order_id = market.order_id(
    ADDRESS,                          # address
    0,                                # subaccount number
    random.randint(0, 100000000),    # chosen client ID
    OrderFlags.SHORT_TERM             # short-term order
)
```

---

#### Step 3: Build the Order

Orders can be **short-term** or **long-term**.

**Order Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `order_type` | OrderType | MARKET, LIMIT, STOP, TAKE_PROFIT |
| `side` | OrderSide | BUY or SELL |
| `size` | Decimal | Quantity being traded |
| `price` | Decimal | Chosen price |
| `time_in_force` | TimeInForce | Execution option |
| `reduce_only` | Boolean | Can only reduce position size |
| `good_til_block` | Integer | Order validity |

**Time in Force Options**:
- `TIME_IN_FORCE_UNSPECIFIED` - Default
- `TIME_IN_FORCE_IOC` - Immediate or Cancel
- `TIME_IN_FORCE_FOK` - Fill or Kill
- `TIME_IN_FORCE_POST_ONLY` - Post Only

**Good Until Block**:
- **Short-term**: Current block height + ShortBlockWindow (20 blocks ≈ 30 seconds)
- **Long-term**: Current block time + StatefulOrderTimeWindow (95 days)

```python
# Get current block height
good_til_block = await node.latest_block_height() + 10

# Create the order
order = market.order(
    order_id,
    OrderType.LIMIT,
    Order.Side.SIDE_BUY,
    size=0.01,           # ETH
    price=1000,          # USDC
    time_in_force=Order.TimeInForce.TIME_IN_FORCE_UNSPECIFIED,
    reduce_only=False,
    good_til_block=good_til_block,  # valid until this block
)
```

---

#### Step 4: Broadcast the Order

Push the order to the dYdX network:

```python
# Broadcast the order
place = await node.place_order(wallet, order)
```

**Response**: Transaction hash and confirmation

---

### Cancel an Order

```python
async def cancel_order(
    self,
    wallet: Wallet,
    order_id: OrderId,
    good_til_block: int = None,
    good_til_block_time: int = None,
    tx_options: Optional[TxOptions] = None,
)
```

---

### Batch Cancel Orders

Cancel multiple short-term orders:

```python
async def batch_cancel_orders(
    self,
    wallet: Wallet,
    subaccount_id: SubaccountId,
    short_term_cancels: List[OrderBatch],
    good_til_block: int,
    tx_options: Optional[TxOptions] = None,
)
```

---

## Indexer API

### Accounts

#### Get Subaccounts

Retrieves list of subaccounts for a given address.

```python
async def get_subaccounts(
    self,
    address: str,
    limit: Optional[int] = None,
) -> Any
```

**Parameters**:
- `address` (required): Primary address
- `limit` (optional): Maximum number of subaccounts

**Response**: List of subaccounts

---

#### Get Subaccount

Retrieves specific subaccount.

```python
async def get_subaccount(
    self,
    address: str,
    subaccount_number: int,
) -> Any
```

**Parameters**:
- `address` (required): Wallet address
- `subaccount_number` (required): Subaccount number

**Response**: Subaccount data with equity, collateral, margin

---

#### List Positions

Retrieves perpetual positions for a subaccount.

```python
async def get_subaccount_perpetual_positions(
    self,
    address: str,
    subaccount_number: int,
    status: Optional[PositionStatus] = None,
    limit: Optional[int] = None,
    created_before_or_at_height: Optional[int] = None,
    created_before_or_at: Optional[str] = None,
) -> Any
```

**Parameters**:
- `address` (required): Wallet address
- `subaccount_number` (required): Subaccount number
- `status` (optional): OPEN, CLOSED, LIQUIDATED
- `limit` (optional): Max results
- `created_before_or_at_height` (optional): Block height filter
- `created_before_or_at` (optional): Timestamp filter (ISO 8601)

**Response**: List of perpetual positions

---

#### Get Asset Positions

Retrieves asset positions for a subaccount.

```python
async def get_subaccount_asset_positions(
    self,
    address: str,
    subaccount_number: int,
    status: Optional[PositionStatus] = None,
    limit: Optional[int] = None,
    created_before_or_at_height: Optional[int] = None,
    created_before_or_at: Optional[str] = None,
) -> Any
```

---

#### List Orders

Retrieves orders for a subaccount.

```python
async def get_subaccount_orders(
    self,
    address: str,
    subaccount_number: int,
    ticker: Optional[str] = None,
    ticker_type: TickerType = TickerType.PERPETUAL,
    side: Optional[OrderSide] = None,
    status: Optional[OrderStatus] = None,
    type: Optional[OrderType] = None,
    limit: Optional[int] = None,
    good_til_block_before_or_at: Optional[int] = None,
    good_til_block_time_before_or_at: Optional[str] = None,
    return_latest_orders: Optional[bool] = None,
) -> Any
```

---

#### Get Transfers

Retrieves transfer history for a subaccount.

```python
async def get_subaccount_transfers(
    self,
    address: str,
    subaccount_number: int,
    limit: Optional[int] = None,
    created_before_or_at_height: Optional[int] = None,
    created_before_or_at: Optional[str] = None,
) -> Any
```

---

### Markets

#### Get Perpetual Markets

Retrieves perpetual markets.

```python
def get_perpetual_markets(self, market: str = None) -> Response
```

**Parameters**:
- `market` (optional): Filter by ticker (e.g., "BTC-USD")

**Response**: Market data including:
- Market ID
- Ticker
- Atomic resolution
- Display decimals
- Step base quantums
- Subticks per tick
- Margin fractions
- Max position size
- Funding rate
- Open interest

**API Example**: `https://indexer.v4testnet.dydx.exchange/v4/perpetualMarkets`

---

#### Get Perpetual Market Orderbook

Retrieves orderbook for a specific market.

```python
async def get_perpetual_market_orderbook(
    self,
    market: str,
) -> dict
```

**Parameters**:
- `market` (required): Market ticker

**Response**: Order book with bids and asks

**API Example**: `https://indexer.v4testnet.dydx.exchange/v4/orderbooks/perpetualMarket/BTC-USD`

---

#### Get Trades

Retrieves trades for a market.

```python
async def get_perpetual_market_trades(
    self,
    market: str,
    starting_before_or_at_height: Optional[int] = None,
    limit: Optional[int] = None,
) -> dict
```

**Parameters**:
- `market` (required): Market ticker
- `starting_before_or_at_height` (optional): Block height filter
- `limit` (optional): Max results

**Response**: List of trades

**API Example**: `https://indexer.v4testnet.dydx.exchange/v4/trades/perpetualMarket/BTC-USD`

---

#### Get Candles

Retrieves candle data for a market.

```python
async def get_perpetual_market_candles(
    self,
    market: str,
    resolution: str,
    from_iso: Optional[str] = None,
    to_iso: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict
```

**Parameters**:
- `market` (required): Market ticker
- `resolution` (required): Candle resolution (1MIN, 5MINS, 15MINS, 30MINS, 1HOUR, 4HOUR, 1DAY)
- `from_iso` (optional): Start time (ISO 8601)
- `to_iso` (optional): End time (ISO 8601)
- `limit` (optional): Max results

**Response**: Candle data

**API Example**: `https://indexer.v4testnet.dydx.exchange/v4/candles/perpetualMarkets/BTC-USD?resolution=1DAY`

---

## Node Client API

### Private API - Place Order

Execute a transaction that places an order.

```python
async def place_order(
    self,
    wallet: Wallet,
    order: Order,
    tx_options: Optional[TxOptions] = None,
)
```

**Parameters**:
- `wallet` (required): Wallet for authentication
- `order` (required): Order object
- `tx_options` (optional): Transaction options

**Response**: Transaction hash

---

### Private API - Cancel Order

Terminate an existing order.

```python
async def cancel_order(
    self,
    wallet: Wallet,
    order_id: OrderId,
    good_til_block: int = None,
    good_til_block_time: int = None,
    tx_options: Optional[TxOptions] = None,
)
```

**Parameters**:
- `wallet` (required): Wallet for authentication
- `order_id` (required): Order ID to cancel
- `good_til_block` (optional): Block validity
- `good_til_block_time` (optional): Time validity
- `tx_options` (optional): Transaction options

**Response**: Transaction hash

---

### Private API - Batch Cancel Orders

Cancel multiple short-term orders.

```python
async def batch_cancel_orders(
    self,
    wallet: Wallet,
    subaccount_id: SubaccountId,
    short_term_cancels: List[OrderBatch],
    good_til_block: int,
    tx_options: Optional[TxOptions] = None,
)
```

---

### Private API - Deposit

Deposit funds to account.

```python
async def deposit(
    self,
    wallet: Wallet,
    subaccount_id: SubaccountId,
    amount: str,
    tx_options: Optional[TxOptions] = None,
)
```

---

### Private API - Withdraw

Withdraw funds from account.

```python
async def withdraw(
    self,
    wallet: Wallet,
    subaccount_id: SubaccountId,
    amount: str,
    tx_options: Optional[TxOptions] = None,
)
```

---

### Private API - Transfer

Transfer between subaccounts.

```python
async def transfer(
    self,
    wallet: Wallet,
    source_subaccount_id: SubaccountId,
    recipient_subaccount_id: SubaccountId,
    amount: str,
    tx_options: Optional[TxOptions] = None,
)
```

---

## WebSocket API

### Connection

**Testnet**: `wss://indexer.v4testnet.dydx.exchange/v4/ws`  
**Mainnet**: `wss://indexer.dydx.trade/v4/ws`

---

### Common Schemas

#### Subscribe

```json
{
  "type": "subscribe",
  "channel": "v4_accounts",
  "id": "dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art"
}
```

#### Unsubscribe

```json
{
  "type": "unsubscribe",
  "channel": "v4_accounts",
  "id": "dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art"
}
```

---

### Channels

#### Subaccounts Channel

Real-time account updates (balance, equity, collateral changes).

```json
{
  "type": "subscribe",
  "channel": "v4_accounts",
  "id": "dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art"
}
```

---

#### Markets Channel

Real-time market data updates.

```json
{
  "type": "subscribe",
  "channel": "v4_markets",
  "id": "BTC-USD"
}
```

---

#### Trades Channel

Real-time trade updates for a market.

```json
{
  "type": "subscribe",
  "channel": "v4_trades",
  "id": "BTC-USD"
}
```

---

#### Orders Channel

Real-time order updates for an account.

```json
{
  "type": "subscribe",
  "channel": "v4_orders",
  "id": "dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art"
}
```

---

#### Candles Channel

Real-time candle updates.

```json
{
  "type": "subscribe",
  "channel": "v4_candles",
  "id": "BTC-USD/1DAY"
}
```

---

#### Block Height Channel

Real-time block height updates.

```json
{
  "type": "subscribe",
  "channel": "v4_blockheight"
}
```

---

## Key Concepts

### Accounts and Subaccounts

- Each wallet address can have multiple subaccounts
- Subaccounts are identified by address + subaccount number
- Default subaccount is 0
- Each subaccount has independent positions and balances

---

### Order Types

1. **Market Orders**: Execute immediately at current market price
2. **Limit Orders**: Execute at specified price or better
3. **Stop Orders**: Trigger when price reaches level
4. **Take Profit Orders**: Close position at profit target

---

### Order Validity

**Short-term Orders**:
- Valid for ~30 seconds (20 blocks)
- Lower fees
- Recommended for most trading

**Long-term Orders**:
- Valid for 95 days
- Higher fees
- For position management

---

### Reduce Only

- When `true`: Order can only decrease position size
- Useful for closing positions
- Prevents accidental position reversal

---

## Best Practices

1. **Use Indexer for Data Queries**: Preferred over Node Client for data
2. **Use Node Client for Trading**: Required for placing/canceling orders
3. **Handle Reconnections**: Implement exponential backoff for WebSocket
4. **Validate Inputs**: Check market exists, order size valid, etc.
5. **Use Short-term Orders**: Default choice for most trading
6. **Monitor Block Height**: Important for order validity
7. **Test on Testnet First**: Always test before mainnet

---

## Resources

- **Official Docs**: https://docs.dydx.xyz/
- **Python Quick Start**: https://docs.dydx.xyz/interaction/client/quick-start-py
- **Trading Guide**: https://docs.dydx.xyz/interaction/trading
- **Indexer API**: https://docs.dydx.xyz/indexer-client/http
- **Node Client**: https://docs.dydx.xyz/node-client
- **WebSocket API**: https://docs.dydx.xyz/indexer-client/websockets
- **GitHub Clients**: https://github.com/dydxprotocol/v4-clients

---

**Last Updated**: October 31, 2025  
**Documentation Version**: October 2025  
**dYdX API Version**: V4
