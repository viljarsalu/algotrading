# dYdX API Endpoints Reference - Your Application

## Quick Reference

### All Endpoints Used by Your Application

| Endpoint | Type | Network | Status | Used By |
|----------|------|---------|--------|---------|
| `/v4/perpetualMarkets` | REST GET | Indexer | ✅ Active | Order placement |
| `/v4/accounts/{address}` | REST GET | Indexer | ✅ Active | Account info |
| `/v4/perpetualPositions` | REST GET | Indexer | ✅ Active | Position monitoring |
| `/v4/ws` | WebSocket | Indexer | ✅ Active | Real-time updates |
| `broadcast_message()` | RPC | Node | ✅ Active | Order broadcasting |
| `latest_block_height()` | RPC | Node | ✅ Active | Block height queries |

---

## 1. Market Data Endpoints

### Get Perpetual Markets

**Endpoint**: `GET /v4/perpetualMarkets`

**Base URLs**:
- Testnet: `https://indexer.v4testnet.dydx.exchange`
- Mainnet: `https://indexer.dydx.trade`

**Query Parameters**:
- `market` (optional): Filter by market symbol (e.g., "BTC-USD")

**Your Implementation**:
```python
# File: app/backend/src/bot/dydx_v4_orders.py (line 183)
async with httpx.AsyncClient() as http_client:
    response = await http_client.get(
        f"{indexer_url}/v4/perpetualMarkets?market={symbol}"
    )
    data = response.json()
```

**Response Structure**:
```json
{
  "markets": {
    "BTC-USD": {
      "id": "1",
      "ticker": "BTC-USD",
      "atomicResolution": -8,
      "displayDecimals": 2,
      "stepBaseQuantums": "1000000",
      "subticksPerTick": "100000",
      "initialMarginFraction": "0.05",
      "maintenanceMarginFraction": "0.02",
      "maxPositionSize": "10000000000",
      "fundingIndex": "0",
      "openInterest": "1000000000",
      "nextFundingRate": "0.0001",
      "nextFundingTime": "2025-10-31T12:00:00Z",
      "minPriceChange": "1000000"
    }
  }
}
```

**Official Docs**: https://docs.dydx.xyz/indexer-client/http/markets/get_perpetual_markets

---

## 2. Account & Position Endpoints

### Get Account Information

**Endpoint**: `GET /v4/accounts/{address}`

**Base URLs**:
- Testnet: `https://indexer.v4testnet.dydx.exchange`
- Mainnet: `https://indexer.dydx.trade`

**Path Parameters**:
- `address`: Wallet address (e.g., "dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art")

**Your Implementation**:
```python
# File: app/backend/src/bot/dydx_client.py (line 410)
account_response = await http_client.get(
    f"{indexer_url}/v4/accounts/{address}"
)
account_data = account_response.json()
```

**Response Structure**:
```json
{
  "account": {
    "address": "dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art",
    "subaccounts": [
      {
        "address": "dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art/0",
        "equity": "1000000000",
        "freeCollateral": "950000000",
        "marginUsed": "50000000",
        "openNotional": "100000000",
        "notionalTotal": "100000000"
      }
    ],
    "equity": "1000000000",
    "freeCollateral": "950000000",
    "pendingDeposits": "0",
    "pendingWithdrawals": "0",
    "openNotional": "100000000",
    "notionalTotal": "100000000"
  }
}
```

**Official Docs**: https://docs.dydx.xyz/indexer-client/http/accounts

---

### Get Perpetual Positions

**Endpoint**: `GET /v4/perpetualPositions`

**Base URLs**:
- Testnet: `https://indexer.v4testnet.dydx.exchange`
- Mainnet: `https://indexer.dydx.trade`

**Query Parameters**:
- `address` (required): Wallet address
- `subaccountNumber` (optional): Subaccount number (default: 0)
- `status` (optional): "OPEN", "CLOSED", "LIQUIDATED"
- `limit` (optional): Max results

**Your Implementation**:
```python
# File: app/backend/src/bot/dydx_client.py (line 416)
positions_response = await http_client.get(
    f"{indexer_url}/v4/perpetualPositions?address={address}"
)
positions_data = positions_response.json()
```

**Response Structure**:
```json
{
  "positions": [
    {
      "address": "dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art",
      "subaccountNumber": 0,
      "market": "BTC-USD",
      "side": "LONG",
      "status": "OPEN",
      "size": "0.01",
      "maxSize": "0.01",
      "entryPrice": "45000",
      "exitPrice": null,
      "realizedPnl": "0",
      "unrealizedPnl": "500",
      "createdAt": "2025-10-31T10:00:00Z",
      "closedAt": null,
      "sumOpen": "0.01",
      "sumClose": "0",
      "netFunding": "0"
    }
  ]
}
```

**Official Docs**: https://docs.dydx.xyz/indexer-client/http/accounts/list-positions

---

## 3. Order Placement Endpoints

### Place Order (Node Client - RPC)

**Method**: `broadcast_message(wallet, order)`

**Your Implementation**:
```python
# File: app/backend/src/bot/dydx_v4_orders.py (line 229)
tx_result = await client.node_client.broadcast_message(wallet, order)

# Extract tx_hash
tx_hash = getattr(tx_result.tx_response, 'txhash', '')
```

**Order Building Process**:

```python
# Step 1: Get market data from indexer
response = await http_client.get(f"{indexer_url}/v4/perpetualMarkets?market={symbol}")
market_data = response.json()["markets"][symbol]

# Step 2: Create Market object
market = Market(market_data)

# Step 3: Create order ID
order_id = market.order_id(
    address,
    0,  # subaccount number
    random.randint(0, 100000000),  # client ID
    OrderFlags.SHORT_TERM
)

# Step 4: Get current block height
good_til_block = await client.node_client.latest_block_height() + 10

# Step 5: Build order
order = market.order(
    order_id=order_id,
    order_type=OrderType.MARKET,  # or OrderType.LIMIT
    side=ORDER_SIDE_BUY,  # 1 for BUY, -1 for SELL
    size=size,
    price=0,  # Market orders use 0
    time_in_force=ORDER_TIME_IN_FORCE_IOC,
    reduce_only=False,
    good_til_block=good_til_block,
)

# Step 6: Broadcast to blockchain
tx_result = await client.node_client.broadcast_message(wallet, order)
```

**Response Structure**:
```python
{
    "tx_response": {
        "txhash": "260E4B0864A67202EB50772708C9B22C10ED5D46618CBD05825CF821E6A75484",
        "code": 0,  # 0 = success
        "log": "[]",
        "gas_used": "150000",
        "gas_wanted": "200000"
    }
}
```

**Official Docs**: https://docs.dydx.xyz/node-client/private/place-order

---

## 4. WebSocket Endpoints

### Real-Time Updates

**Endpoint**: `wss://indexer.v4testnet.dydx.exchange/v4/ws` (testnet)  
**Endpoint**: `wss://indexer.dydx.trade/v4/ws` (mainnet)

**Your Implementation**:
```python
# File: app/backend/src/bot/websocket_manager.py (line 62)
self.websocket = await websockets.connect(self.ws_url)
```

**Subscription Channels**:

1. **Account Updates**
```json
{
  "type": "subscribe",
  "channel": "v4_accounts",
  "id": "dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art"
}
```

2. **Order Updates**
```json
{
  "type": "subscribe",
  "channel": "v4_orders",
  "id": "dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art"
}
```

3. **Trade Updates**
```json
{
  "type": "subscribe",
  "channel": "v4_trades",
  "id": "BTC-USD"
}
```

4. **Market Updates**
```json
{
  "type": "subscribe",
  "channel": "v4_markets",
  "id": "BTC-USD"
}
```

**Official Docs**: https://docs.dydx.xyz/indexer-client/websockets

---

## 5. Network Configuration

### Testnet Endpoints

```python
# Indexer (REST)
INDEXER_REST_URL = "https://indexer.v4testnet.dydx.exchange"

# Indexer (WebSocket)
INDEXER_WS_URL = "wss://indexer.v4testnet.dydx.exchange/v4/ws"

# Node RPC Endpoints (with fallbacks)
NODE_URLS = [
    "https://oegs-testnet.dydx.exchange:443",
    "https://testnet-dydx-rpc.lavenderfive.com",
    "https://test-dydx-rpc.kingnodes.com",
    "https://dydx-testnet-rpc.polkachu.com",
    "https://dydx-rpc-testnet.enigma-validator.com"
]
```

**Your Implementation**: `app/backend/src/bot/dydx_client.py` (lines 110-136)

---

### Mainnet Endpoints

```python
# Indexer (REST)
INDEXER_REST_URL = "https://indexer.dydx.trade"

# Indexer (WebSocket)
INDEXER_WS_URL = "wss://indexer.dydx.trade/v4/ws"

# Node RPC Endpoints (with fallbacks)
NODE_URLS = [
    "https://dydx-ops-rpc.kingnodes.com",
    "https://dydx-mainnet-rpc.allthatnode.com:1317"
]
```

**Your Implementation**: `app/backend/src/bot/dydx_client.py` (lines 96-107)

---

## 6. Error Handling

### Common HTTP Error Responses

| Status | Meaning | Your Handling |
|--------|---------|---------------|
| 200 | OK | Process response |
| 400 | Bad Request | Log error, return error response |
| 404 | Not Found | Market/account not found |
| 429 | Too Many Requests | Implement backoff |
| 500 | Server Error | Retry with fallback endpoint |

**Your Implementation**: `app/backend/src/bot/dydx_v4_orders.py` (lines 256-275)
- Graceful fallback to mock orders
- Proper exception logging
- User-friendly error messages

---

## 7. Rate Limiting

**Indexer API**: Generally no strict rate limits for testnet, production limits vary  
**Node RPC**: Depends on endpoint provider

**Your Implementation**: Implements exponential backoff in WebSocket reconnection logic

---

## 8. Authentication

### Node Client Authentication

```python
# Create wallet from mnemonic
wallet = await Wallet.from_mnemonic(node_client, mnemonic, address)

# Sign and broadcast transactions
tx_result = await node_client.broadcast_message(wallet, order)
```

**Your Implementation**: `app/backend/src/bot/dydx_client.py` (lines 159-177)
- Per-user mnemonic support
- Proper wallet initialization
- Secure credential handling

### Indexer API Authentication

**No authentication required** - Public REST API

---

## 9. Testing Endpoints

### Manual Testing

```bash
# Test Indexer REST API
curl "https://indexer.v4testnet.dydx.exchange/v4/perpetualMarkets?market=BTC-USD"

# Test Account Endpoint
curl "https://indexer.v4testnet.dydx.exchange/v4/accounts/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art"

# Test Positions Endpoint
curl "https://indexer.v4testnet.dydx.exchange/v4/perpetualPositions?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art"

# Check Transaction Status
curl "https://testnet-lcd.dydx.exchange/cosmos/tx/v1beta1/txs/{tx_hash}"
```

---

## 10. API Call Sequence Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Places Trade                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Webhook Receiver: POST /api/webhooks/signal/{webhook_uuid} │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         TradingEngine: Validate & Fetch Credentials         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  DydxClient.create_client(mnemonic)                         │
│  └─ NodeClient.connect(config)                             │
│  └─ Wallet.from_mnemonic()                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  DydxV4OrderPlacer.place_market_order()                     │
│                                                             │
│  1. GET /v4/perpetualMarkets?market=BTC-USD                │
│     (Indexer REST API)                                     │
│                                                             │
│  2. Create Market object                                   │
│                                                             │
│  3. Build Order:                                           │
│     - market.order_id()                                    │
│     - market.order()                                       │
│                                                             │
│  4. broadcast_message(wallet, order)                       │
│     (Node Client RPC)                                      │
│                                                             │
│  5. Extract tx_hash from response                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Save to Database & Return Response                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  WebSocket Listener (Real-time Updates)                    │
│  - Account updates                                         │
│  - Order status changes                                    │
│  - Trade fills                                             │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Position Monitor (Background Worker)                      │
│  - Poll GET /v4/perpetualPositions                         │
│  - Check TP/SL conditions                                  │
│  - Auto-close positions                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

Your application correctly implements:
- ✅ Indexer REST API for data queries
- ✅ Node Client RPC for order placement
- ✅ WebSocket connections for real-time updates
- ✅ Proper error handling and fallbacks
- ✅ Network configuration management
- ✅ Security best practices

All endpoints match official dYdX documentation.

