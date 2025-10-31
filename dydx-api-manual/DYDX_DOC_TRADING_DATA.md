Title: Accounts

URL Source: https://docs.dydx.xyz/interaction/data/accounts

Markdown Content:
All of your trading activity is associated with your account which corresponds to an address. In dYdX, accounts are also composed by subaccounts. All trading is done through a subaccount. See more on the [Accounts and Subaccounts](https://docs.dydx.xyz/concepts/trading/accounts) page.

Account Data
------------

An account can have multiple subaccounts. To fetch all known (with some activity) subaccounts associated with an account the account's address is required.

Python

`response = await indexer.account.get_subaccounts(ADDRESS)`

To fetch a specific subaccount, use the account's address the the subaccount number.

Python

```
# Fetch subaccount '0' information.
subaccount_resp = await indexer.account.get_subaccount(ADDRESS, 0)
```

### Balance

The responses above will contain information such as the subaccount's equity, also known as the total account value. Your equity is a combination of the account's USDC balance and sum of the open positions values. A minimum amount of funds is required to trade, see more on [Margin](https://docs.dydx.xyz/concepts/trading/margin) and [Equity Tier Limits](https://docs.dydx.xyz/concepts/trading/limits/equity-tier-limits).

Python

```
subaccount = subaccount_resp["subaccount"]
print("Equity: ", subaccount["equity"])
print("Open positions: ", subaccount["openPerpetualPositions"])
```

Asset Transfers
---------------

Methods are available to transfer [assets](https://docs.dydx.xyz/concepts/trading/assets#assets-and-collateral) among accounts and subaccounts. See the table below for the different transfer paths. Links point to the API reference.

| Source | Destination | Method |
| --- | --- | --- |
| Account | Subaccount | [Deposit](https://docs.dydx.xyz/node-client/private#deposit) |
| Subaccount | Account | [Withdraw](https://docs.dydx.xyz/node-client/private#withdraw) |
| Subaccount | Subaccount | [Transfer](https://docs.dydx.xyz/node-client/private#transfer) |
| Account | Account | [Send Token](https://docs.dydx.xyz/node-client/private#send-token) |
Title: Trading Data

URL Source: https://docs.dydx.xyz/interaction/data/market

Published Time: Tue, 21 Oct 2025 21:37:42 GMT

Markdown Content:
This section guides you on how to fetch some important data points. We focus here on getting data using spontaneous (single) requests. For continuous data streams of data see also the [WebSockets guide](https://docs.dydx.xyz/interaction/data/feeds).

List Positions
--------------

Assets are used to trade and manage (perpetual) positions opened and closed by [issuing orders](https://docs.dydx.xyz/interaction/trading#place-an-order). See the example below on how to check your perpetual positions.

Python

```
from dydx_v4_client.indexer.rest.constants import PositionStatus
 
# Fetch all subaccount '0' positions.
perpetual_positions_response = await indexer 
    .account 
    .get_subaccount_perpetual_positions(ADDRESS, 0) 
 
# Fetch only open positions. 
perpetual_positions_response = await indexer
    .account
    .get_subaccount_perpetual_positions(address, 0, PositionStatus.OPEN)
```

See the [API reference](https://docs.dydx.xyz/indexer-client/http/accounts/list_positions) for the complete method definition.

Market List
-----------

A market (sometimes referred by the ticker name, e.g., `ETH-USD`) is associated with a perpetual and it is the place where trading happens. To fetch the available markets see the code below.

Python

```
response = await indexer.markets.get_perpetual_markets() 
print(response["markets"])
```

See the [API reference](https://docs.dydx.xyz/indexer-client/http/markets/get_perpetual_markets) for the complete method definition.

List Orders
-----------

Retrieve orders for a specific subaccount, with various filtering options to narrow down the results based on order characteristics.

Python

`orders_response = indexer.account.get_subaccount_orders(address, 0)`

See the [API reference](https://docs.dydx.xyz/indexer-client/http/accounts/list_orders) the complete method definition.

Get Fills
---------

Retrieve order fill records for a specific subaccount on the exchange. Fills are matched orders.

Python

`fills_response = indexer.account.get_subaccount_fills(address, 0)`

See the [API reference](https://docs.dydx.xyz/indexer-client/http/accounts/get_fills) the complete method definition.

Price History
-------------

Price history in the classic [candlestick](https://en.wikipedia.org/wiki/Candlestick_chart) can also be fetched. Data will be organized into a _open_, _high_, _low_, and _close_ (OHLC) prices for some _period_.

Python

```
from dydx_v4_client.indexer.candles_resolution import CandlesResolution
response = await indexer.markets.get_perpetual_market_candles( 
    market="BTC-USD", resolution=CandlesResolution.ONE_MINUTE
) 
print(response["candles"])
```

See the [API reference](https://docs.dydx.xyz/indexer-client/http/markets/get_candles) for the complete method definition.

Get User Fee Tier
-----------------

The Get User Fee Tier function retrieves the perpetual fee tier associated with a specific wallet address, providing information on the user's current fee structure.

Python

`user_fee_tier = await node.get_user_fee_tier(ADDRESS)`

See the [API reference](https://docs.dydx.xyz/node-client/public/get_user_fee_tier) for the complete method definition.

Get Rewards Params
------------------

The Get Rewards Params function retrieves the parameters for the rewards system, providing insight into the set configurations for earning and distributing rewards.

Python

`rewards_params = await node.get_rewards_params()`

See the [API reference](https://docs.dydx.xyz/node-client/public/get_rewards_params) for the complete method definition.

Trading Rewards
---------------

Retrieve historical block trading rewards for the specified address.

Python

`response = await indexer.account.get_historical_block_trading_rewards(test_address, limit)`

See the [API reference](https://docs.dydx.xyz/indexer-client/http/accounts/get_rewards) for the complete method definition.

Get Latest Block Height
-----------------------

Retrieve the most recent block's height. This can serve to see if the blockchain node you are connected to is in sync.

Python

`height = await node.latest_block_height()`

See the [API reference](https://docs.dydx.xyz/node-client/public/get_latest_block_height) for the complete method definition.
Title: WebSockets

URL Source: https://docs.dydx.xyz/interaction/data/feeds

Published Time: Tue, 14 Oct 2025 13:32:36 GMT

Markdown Content:
The Indexer can provide realtime data through its WebSockets endpoint.

Below an example is provided of how to establish a connection and watch realtime **trades** updates. See the full API specification [here](https://docs.dydx.xyz/indexer-client/websockets) for other data feeds.

Connect
-------

To get realtime updates, we first need to establish a connection with the WebSockets endpoint.

Python

```
# The message handler, triggered when a message is received.
def handler(ws: IndexerSocket, message: dict):
    print(message)
```

Upon a successful connection you will receive an initial connection message. This message maybe abstracted away, depending on the client.

Connection response

```
{
  "type": "connected",
  "connection_id": "004a1efa-21bb-4b19-a2e9-a8ffadd6dc53",
  "message_id": 0
}
```

Subscribe
---------

After a connection is established, you may subscribe to several feeds, containing different types of data. WebSockets include information on **markets**, **trades**, **orders**, **candles**, and **subaccounts**.

Python

```
# Modify the `handler()` function.
# Subscribe only after a succesful connection.
def handler(ws: IndexerSocket, message: dict):
  if message["type"] == "connected":
    # Subscribe.
    ws.trades.subscribe(ETH_USD)
  print(message)
```

Handling the data
-----------------

After subscription, you will start receiving the update messages. Here, the update messages contain the finalized trades (matched orders) for the `ETH-USD` ticker.

For each received message, the `handler()` function will be called on it. Modify it to implement your desired logic.

Handling in Rust
In Rust, callbacks are not used. Intead, the handle returned on subscription must be polled.

Rust

```
// Continuous loop running until the feed is stopped.
while let Some(msg) = trades_feed.recv().await {
    println!("New trades update: {msg:?}");
}
```

Unsubscribe
-----------

When the data feed is not needed anymore, you may stop it and unsubscribe from it.

Python

`ws.trades.unsubscribe(ETH_USD)`

Details
-------

### Rate Limiting

The default rate limiting config for WebSockets is:

*   2 subscriptions per (connection + channel + channel ID) per second.
*   2 invalid messages per connection per second.

### Maintaining a Connection

Every 30 seconds, the WebSockets API will send a [heartbeat `ping` control frame](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers#pings_and_pongs_the_heartbeat_of_websockets) to the connected client. If a `pong` event is not received within 10 seconds back, the websocket API will disconnect.

### CLI example

You can use a command-line WebSockets client such as[`interactive-websocket-cli`](https://www.npmjs.com/package/interactive-websocket-cli)to connect and subscribe to channels.

Example (with`interactive-websocket-cli`):

```
# For the deployment by DYDX token holders (mainnet), use
# wscli connect wss://indexer.dydx.trade/v4/ws
wscli connect wss://indexer.v4testnet.dydx.exchange/v4/ws
<output from ws-cli>
<type 's' to send> { "type": "subscribe", "channel": "v4_trades", "id": "BTC-USD" }
```
Title: Watch orderbook

URL Source: https://docs.dydx.xyz/interaction/data/watch-orderbook

Markdown Content:
Depending on your trading strategy, keeping track of the current orderbook can be essential. The orderbook is a list of all the unmatched orders, divided into the **bids** (buy orders) and the **asks** (sell orders).

We'll use the Indexer WebSockets data streams for this.

Subscribe to the Orders channel
-------------------------------

Lets take as reference the previous [section](https://docs.dydx.xyz/interaction/data/feeds). Subscribe to the Orders channel.

Python

```
def handler(ws: IndexerSocket, message: dict):
  if message["type"] == "connected":
      # Subscribe.
      ws.orders.subscribe(ETH_USD) 
  print(message)
```

Parse the update messages
-------------------------

Grab the bids and asks lists from the incoming messages. Each incoming bid and ask entry is the updated _level_ in the orderbook. Each level is associated with a certain price and a total size. The total size is the current aggregated orders size for that price.

Python

```
def handler(ws: IndexerSocket, message: dict):
    if message["type"] == "connected":
        ws.order_book.subscribe(ETH_USD, False)
    elif message["channel"] == "v4_orderbook" and "contents" in message: 
        # Bids levels. 
        if "bids" in contents: 
            for bid in contents["bids"]: 
                price = bid["price"] 
                size = bid["size"] 
        # Asks levels. 
        if "asks" in contents: 
            for ask in contents["asks"]: 
                price = ask["price"] 
                size = ask["size"]
```

Keeping track
-------------

On a continuous loop, keep recording all the incoming bids and asks and update your local orderbook.

Python

```
def handler(ws: IndexerSocket, message: dict):
    if message["type"] == "connected":
        ws.order_book.subscribe(ETH_USD, False)
    elif message["channel"] == "v4_orderbook" and "contents" in message:
        # Modify the above snippet. 
        # For full snapshot (initial subscribed message), reset the orderbook. 
        if message["type"] == "subscribed": 
            orderbook["bids"] = {} 
            orderbook["asks"] = {} 
        # Process bids levels. 
        if "bids" in contents:
            for bid in contents["bids"]:
                process_price_level(bid, "bids") 
 
        # Process asks levels. 
        if "asks" in contents:
            for ask in contents["asks"]:
                process_price_level(ask, "asks") 
 
# Orderbook state. Levels are stored as [price, size, offset]. 
orderbook = { 
    "bids": {}, 
    "asks": {} 
} 
 
def process_price_level(level, side): 
    """Process a single price level (bid or ask)"""
    if isinstance(level, dict): 
        # Full snapshot format 
        price = level["price"] 
        size = level["size"] 
        offset = level.get("offset", "0") 
    else: 
        # Incremental update format 
        price = level[0] 
        size = level[1] 
        offset = level[2] if len(level) > 2 else "0"
 
    # Update local orderbook. 
    if float(size) > 0: 
        orderbook[side][price] = [price, size, offset] 
    elif price in orderbook[side]: 
        del orderbook[side][price]
```

Uncrossing the orderbook
------------------------

Given the decentralized nature of dYdX, sometimes, some of the bids will be higher than some of the asks.

If trader needs the orderbook uncrossed, then one way is to use the order of messages as a logical timestamp. That is, when a message is received, update a global locally-held offset. Each WebSockets update has a `message-id` which is a logical offset to use. Using a timestamp is also an option.

Python

```
# In the handler() function
# ...
        # Process asks levels.
        if "asks" in contents:
            for ask in contents["asks"]:
                process_price_level(ask, "asks")
        
        # Uncross the orderbook.
        uncross_orderbook()
 
def get_sorted_book():
    """Get sorted lists of bids and asks"""
    bids_list = list(orderbook["bids"].values())
    asks_list = list(orderbook["asks"].values())
 
    bids_list.sort(key=lambda x: float(x[0]), reverse=True)
    asks_list.sort(key=lambda x: float(x[0]))
 
    return bids_list, asks_list
 
def uncross_orderbook():
    """Remove crossed orders from the orderbook"""
    bids_list, asks_list = get_sorted_book()
 
    if not bids_list or not asks_list:
        return
 
    top_bid = float(bids_list[0][0])
    top_ask = float(asks_list[0][0])
 
    while bids_list and asks_list and top_bid >= top_ask:
        bid = bids_list[0]
        ask = asks_list[0]
 
        bid_price = float(bid[0])
        ask_price = float(ask[0])
        bid_size = float(bid[1])
        ask_size = float(ask[1])
        bid_offset = int(bid[2]) if len(bid) > 2 else 0
        ask_offset = int(ask[2]) if len(ask) > 2 else 0
 
        if bid_price >= ask_price:
            # Remove older entry.
            if bid_offset < ask_offset:
                bids_list.pop(0)
            elif bid_offset > ask_offset:
                asks_list.pop(0)
            else:
                # Same offset, handle based on size.
                if bid_size > ask_size:
                    asks_list.pop(0)
                    bid[1] = str(bid_size - ask_size)
                elif bid_size < ask_size:
                    ask[1] = str(ask_size - bid_size)
                    bids_list.pop(0)
                else:
                    # Both filled exactly.
                    asks_list.pop(0)
                    bids_list.pop(0)
        else:
            # No crossing.
            break
 
        if bids_list and asks_list:
            top_bid = float(bids_list[0][0])
            top_ask = float(asks_list[0][0])
 
    # Update the orderbook with uncrossed data.
    orderbook["bids"] = {bid[0]: bid for bid in bids_list}
    orderbook["asks"] = {ask[0]: ask for ask in asks_list}
```

Additional logic
----------------

Now with an always up-to-date orderbook, implement your trading strategy based on this data. For simplicity here, we'll just print the current state.

Python

```
def print_orderbook():
    """Print n levels"""
    bids_list, asks_list = get_sorted_book()
 
    print(f"\n--- Orderbook for {ETH_USD} ---")
 
    # Print asks. 
    for price, size in reversed(asks_list): 
        print(f"ASK: {price:<12} | {size:<16}") 
 
    print("----------------") 
 
    # Print bids. 
    for price, size in bids_list: 
        print(f"BID: {price:<12} | {size:<16}") 
 
    print("")
# ... 
print_orderbook()
```
