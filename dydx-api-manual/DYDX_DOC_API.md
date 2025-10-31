Title: Indexer API

URL Source: https://docs.dydx.xyz/indexer-client

Published Time: Tue, 21 Oct 2025 21:44:00 GMT

Warning: This page maybe not yet fully loaded, consider explicitly specify a timeout.
Warning: This page contains shadow DOM that are currently hidden, consider enabling shadow DOM processing.
Warning: This page maybe requiring CAPTCHA, please make sure you are authorized to access this page.

Markdown Content:
[Skip to content](https://docs.dydx.xyz/indexer-client/#vocs-content)

[![Image 1: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

[![Image 2: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

The Indexer is a high-availability system designed to provide structured data. It serves both over its [HTTP/REST API](https://docs.dydx.xyz/indexer-client/http) for spontaneous requests and over its [WebSockets API](https://docs.dydx.xyz/indexer-client/websockets) for continuous data streaming.

See the [guide](https://docs.dydx.xyz/interaction/endpoints#indexer-client) on how to use the available Indexer client to learn how to connect to it.
Title: HTTP API

URL Source: https://docs.dydx.xyz/indexer-client/http

Published Time: Tue, 21 Oct 2025 12:09:25 GMT

Markdown Content:
Accounts
--------

Python

`account = indexer_client.account()`

### Get Subaccounts

Retrieves a list of subaccounts associated with a given address. Subaccounts are related addresses that fall under the authority or ownership of the primary address.

#### Method Declaration

Python

```
async def get_subaccounts(
    self,
    address: str,
    limit: Optional[int] = None,
) -> Any
```

Unification Plan
*   Rust implementation doesn't have optional parameters.

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | path | [Address](https://docs.dydx.xyz/types/address) | true | The primary address for which to retrieve associated subaccounts. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of subaccounts in the response. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [AddressResponse](https://docs.dydx.xyz/types/address_response) | The subaccounts data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/addresses/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art)
### Get Subaccount

Retrieves a specific subaccount associated with a given address and subaccount number.

#### Method Declaration

Python

```
async def get_subaccount(
    self,
    address: str,
    subaccount_number: int,
) -> Any
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The primary address to which the subaccount belongs. |
| `subaccountNumber` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | The specific subaccount number to retrieve. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [SubaccountResponseObject](https://docs.dydx.xyz/types/subaccount_response_object) ⛁ | The subaccount data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/addresses/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art/subaccountNumber/0)
### List Positions

Retrieves perpetual positions for a specific subaccount. Both open and closed/historical positions can be queried.

#### Method Declaration

Python

```
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

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `subaccountNumber` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | The identifier for the specific subaccount within the wallet address. |
| `status` | query | [PerpetualPositionStatus](https://docs.dydx.xyz/types/perpetual_position_status) | false | Filter to retrieve positions with a specific status. If not provided, all positions will be returned regardless of status. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of asset positions to return in the response. |
| `createdBeforeOrAtHeight` | query | [Height](https://docs.dydx.xyz/types/height) | false | Restricts results to positions created at or before a specific blockchain height. |
| `createdBeforeOrAt` | query | [DateTime](https://docs.dydx.xyz/types/date_time) | false | Restricts results to positions created at or before a specific timestamp (ISO 8601 format). |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [PerpetualPositionResponseObject](https://docs.dydx.xyz/types/perpetual_position_response_object) ⛁ | The perpetual positions data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/perpetualPositions?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art&subaccountNumber=0)
Examples: [Guide - List Positions](https://docs.dydx.xyz/interaction/data/market#list-positions)

### Get Asset Positions

Retrieves asset positions and respective details of a specific subaccount.

#### Method Declaration

Python

```
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

Unification Plan
*   Rename all methods to `get_asset_positions` - shorter is better.
*   Add a `Subaccount` pair to Python and JavaScript, since it's always a pair
*   Add options to the Rust version
*   Rename `created_before_or_at_time` parameter to `created_before_or_at`
*   Rename `PerpetualPositionStatus` to `PositionStatus`

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `subaccountNumber` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | The identifier for the specific subaccount within the wallet address. |
| `status` | query | [PerpetualPositionStatus](https://docs.dydx.xyz/types/perpetual_position_status) | false | Filter to retrieve positions with a specific status. If not provided, all positions will be returned regardless of status. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of asset positions to return in the response. |
| `createdBeforeOrAtHeight` | query | [Height](https://docs.dydx.xyz/types/height) | false | Restricts results to positions created at or before a specific blockchain height. |
| `createdBeforeOrAt` | query | [DateTime](https://docs.dydx.xyz/types/date_time) | false | Restricts results to positions created at or before a specific timestamp (ISO 8601 format). |

#### Response

A data structure containing the requested asset positions. Typically includes details such as asset ID, size, side (buy/sell), entry price, realized PnL, and other position-specific information.

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [AssetPositionResponseObject](https://docs.dydx.xyz/types/asset_position_response_object) ⛁ | The asset positions data. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/assetPositions?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art&subaccountNumber=0)
### Get Transfers

Retrieves the transfer history for a specific subaccount.

#### Method Declaration

Python

```
async def get_subaccount_transfers(
    self,
    address: str,
    subaccount_number: int,
    limit: Optional[int] = None,
    created_before_or_at_height: Optional[int] = None,
    created_before_or_at: Optional[str] = None,
) -> Any
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `subaccount_number` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | The identifier for the specific subaccount within the wallet address. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of items in the response. |
| `createdBeforeOrAtHeight` | query | [Height](https://docs.dydx.xyz/types/height) | false | Restricts results to positions created at or before a specific blockchain height. |
| `createdBeforeOrAt` | query | [DateTime](https://docs.dydx.xyz/types/date_time) | false | Restricts results to positions created at or before a specific timestamp. |
| `page` | query | [u32](https://docs.dydx.xyz/types/u32) | false | The page number for paginated results. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/OK) | [TransferResponseObject](https://docs.dydx.xyz/types/transfer_response_object) ⛁ | The transfers data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/transfers?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art&subaccountNumber=0)
### Get Transfers Between

Fetch information regarding a transfer between two subaccounts.

#### Method Declaration

Python

```
async def get_transfer_between(
    self,
    source_address: str,
    source_subaccount_number: int,
    recipient_address: str,
    recipient_subaccount_number: int,
    created_before_or_at_height: Optional[int] = None,
    created_before_or_at: Optional[str] = None,
) -> Any
```

Unification Plan
*   Response object does not have defined structure in TypeScript client. Will have to work on it.

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `sourceAddress` | query | string | true | Sender's wallet address |
| `sourceSubaccountNumber` | query | string | true | The identifier for the specific subaccount within the sender wallet address. |
| `recipientAddress` | query | string | true | Receiver wallet address |
| `recipientSubaccountNumber` | query | string | true | The identifier for the specific subaccount within the receiver wallet address. |
| `createdBeforeOrAtHeight` | query | number | false | Restricts results to positions created at or before a specific blockchain height. |
| `createdBeforeOrAt` | query | string | false | Restricts results to positions created at or before a specific timestamp (ISO 8601 format). |

#### Response

### List Orders

Retrieves orders for a specific subaccount, with various filtering options to narrow down the results based on order characteristics.

#### Method Declaration

Python

```
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

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `subaccountNumber` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | The identifier for the specific subaccount within the wallet address. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of asset positions to return in the response. |
| `ticker` | query | [Ticker](https://docs.dydx.xyz/types/ticker) | false | The ticker filter. |
| `side` | query | [OrderSide](https://docs.dydx.xyz/types/order_side) | false | The order side filter. |
| `status` | query | [OrderStatus](https://docs.dydx.xyz/types/order_status) | false | The order status filter. |
| `type` | query | [OrderType](https://docs.dydx.xyz/types/order_type) | false | The order type filter. |
| `goodTilBlockBeforeOrAt` | query | [Height](https://docs.dydx.xyz/types/height) | false | The block number filter for orders good until before or at. |
| `goodTilBlockTimeBeforeOrAt` | query | [DateTime in UTC](https://docs.dydx.xyz/types/date_time) | false | The timestamp filter for orders good until before or at. |
| `returnLatestOrders` | query | bool | false | Whether to return only the latest orders. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [OrderResponseObject](https://docs.dydx.xyz/types/order_response_object) ⛁ | The orders data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/orders?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art&subaccountNumber=0)
Examples: [Guide - List Orders](https://docs.dydx.xyz/interaction/data/market#list-orders)

### Get Order

Retrieves detailed information about a specific order based on its unique identifier (the order ID). To get the order ID, see how to [create](https://docs.dydx.xyz/interaction/trading#identifying-the-order) it or fetch the [order history](https://docs.dydx.xyz/indexer-client/http#list-orders).

#### Method Declaration

Python

```
async def get_order(
    self,
    order_id: str,
) -> Any
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `orderId` | path | [OrderId](https://docs.dydx.xyz/types/order_id) | true | The order ID. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [OrderResponseObject](https://docs.dydx.xyz/types/order_response_object) ⛁ | The order data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The order was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/orders/66390c15-ebad-53f8-86ad-99b3dfedbc85)
### Get Fills

Retrieves fill records for a specific subaccount on the exchange. A fill represents a trade that has been executed.

#### Method Declaration

Python

```
async def get_subaccount_fills(
    self,
    address: str,
    subaccount_number: int,
    ticker: Optional[str] = None,
    ticker_type: TickerType = TickerType.PERPETUAL,
    limit: Optional[int] = None,
    created_before_or_at_height: Optional[int] = None,
    created_before_or_at: Optional[str] = None,
) -> Any
```

Unification Plan
*   Rename all methods to `get_fills` - shorter is better.
*   Add a `Subaccount` pair to Python and JavaScript, since it's always a pair
*   Rename `created_before_or_at_time` parameter to `created_before_or_at`
*   `page` optional parameter is missing in Python
*   `page` optional parameter is missing in Rust
*   In Rust `market` field of the options struct must be `ticker`
*   In Rust `market_type` field of the options struct must be `ticker_type`

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `subaccountNumber` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | The identifier for the specific subaccount within the wallet address. |
| `ticker` | query | [Ticker](https://docs.dydx.xyz/types/ticker) | false | The market symbol to filter fills by (e.g., "BTC-USD"). If not provided, fills for all markets will be returned. |
| `tickerType` | query | [MarketType](https://docs.dydx.xyz/types/market_type) | false | The type of market to filter by. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of asset positions to return in the response. |
| `createdBeforeOrAtHeight` | query | [Height](https://docs.dydx.xyz/types/height) | false | Filters results to positions created at or before a specific blockchain height. |
| `createdBeforeOrAt` | query | [DateTime](https://docs.dydx.xyz/types/date_time) | false | Filters results to positions created at or before a specific timestamp (ISO 8601 format). |
| `page` | query | [u32](https://docs.dydx.xyz/types/u32) | false | The page number for paginated results. |

#### Response

A promise that resolves to fill data containing details such as order ID, market, side (buy/sell), size, price, execution time, and other fill-specific information.

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [FillResponseObject](https://docs.dydx.xyz/types/fill_response_object) ⛁ | The fills data. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/fills?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art&subaccountNumber=0)
Examples: [Guide - Get Fills](https://docs.dydx.xyz/interaction/data/market#get-fills)

### Get Historical PNL

Retrieves historical profit and loss (PNL) data for a specific subaccount on the exchange. These records provide insights into the trading performance over time.

#### Method Declaration

Python

```
async def get_subaccount_historical_pnls(
    self,
    address: str,
    subaccount_number: int,
    effective_before_or_at: Optional[str] = None,
    effective_at_or_after: Optional[str] = None,
) -> Any
```

Unification Plan
*   Parameter `created_on_or_after_height` is missing
*   Parameter `created_on_or_after` is missing

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `subaccount_number` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | The identifier for the specific subaccount within the wallet address. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of asset positions to return in the response. |
| `createdBeforeOrAtHeight` | query | [Height](https://docs.dydx.xyz/types/height) | false | Filters results to positions created at or before a specific blockchain height. |
| `createdBeforeOrAt` | query | [DateTime in UTC](https://docs.dydx.xyz/types/date_time) | false | Filters results to positions created at or before a specific timestamp (ISO 8601 format). |
| `createdOnOrAfterHeight` | query | [Height](https://docs.dydx.xyz/types/height) | false | Filters results to positions created on or after a specific blockchain height. |
| `createdOnOrAfter` | query | [DateTime in UTC](https://docs.dydx.xyz/types/date_time) | false | Filters results to positions created on or after a specific timestamp (ISO 8601 format). |
| `page` | query | [u32](https://docs.dydx.xyz/types/u32) | false | The page number for paginated results. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [PnlTicksResponseObject](https://docs.dydx.xyz/types/pnl_ticks_response_object) ⛁ | The historical PnLs data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/historical-pnl?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art&subaccountNumber=0)
### Get Rewards

Retrieves historical block trading rewards for the specified address.

#### Method Declaration

Python

```
async def get_historical_block_trading_rewards(
    self,
    address: str,
    limit: Optional[int] = None,
) -> Any
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | path | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of asset positions to return in the response. |
| `startingBeforeOrAtHeight` | query | [Height](https://docs.dydx.xyz/types/height) | false | The timestamp filter for rewards starting before or at. |
| `startingBeforeOrAt` | query | [DateTime in UTC](https://docs.dydx.xyz/types/date_time) | false | The block height filter for rewards starting before or at. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [HistoricalBlockTradingReward](https://docs.dydx.xyz/types/historical_block_trading_reward) ⛁ | The historical block trading rewards data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/historicalBlockTradingRewards/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art)
### Get Rewards Aggregated

Retrieves aggregated historical trading rewards for the specified address.

#### Method Declaration

Python

```
async def get_historical_trading_rewards_aggregated(
    self,
    address: str,
    period: TradingRewardAggregationPeriod = TradingRewardAggregationPeriod.DAILY,
    limit: Optional[int] = None,
    starting_before_or_at: Optional[str] = None,
    starting_before_or_at_height: Optional[int] = None,
) -> Any
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | path | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `period` | query | [TradingRewardAggregationPeriod](https://docs.dydx.xyz/types/trading_reward_aggregation_period) | true | The aggregation period. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | The maximum number of aggregated rewards to retrieve. |
| `startingBeforeOrAt` | query | [DateTime](https://docs.dydx.xyz/types/date_time) | false | The timestamp filter for rewards starting before or at. |
| `startingBeforeOrAtHeight` | query | [Height](https://docs.dydx.xyz/types/height) | false | The block height filter for rewards starting before or at. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [HistoricalTradingRewardAggregation](https://docs.dydx.xyz/types/historical_trading_reward_aggregation) ⛁ | The aggregated historical trading rewards data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/historicalTradingRewardAggregations/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art?period=DAILY)
### Get Parent Subaccount

Query for the parent subaccount, its child subaccounts, equity, collateral and margin. See more information on parent subaccounts [here](https://docs.dydx.xyz/concepts/trading/isolated-positions#parent-subaccounts). e.g. parent subaccount 0 has child subaccounts 128, 256,...

#### Method Declaration

Python

```
async def get_parent_subaccount(
    self,
    address: str,
    subaccount_number: int,
) -> Any
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | path | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the parent subaccount. |
| `number` | path | [SubaccountNumber] | true | The identifier for the specific subaccount within the wallet address. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [ParentSubaccountResponseObject](https://docs.dydx.xyz/types/parent_subaccount_response_object) ⛁ | The parent subaccount data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The parent subaccount was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/addresses/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art/parentSubaccountNumber/0)
### List Parent Positions

List all positions of a parent subaccount.

#### Method Declaration

Python

```
async def list_parent_orders(
    self,
    address: str,
    subaccount_number: int,
    limit: Optional[int] = None,
    ticker: Optional[str] = None,
    side: Optional[OrderSide] = None,
    status: Optional[OrderStatus] = None,
    order_type: Optional[OrderType] = None,
    good_til_block_before_or_at: Optional[int] = None,
    good_til_block_time_before_or_at: Optional[str] = None,
    return_latest_orders: Optional[bool] = None,
) -> Any
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `parentSubaccountNumber` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | Subaccount number of the parent subaccount. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of asset positions to return in the response. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [PerpetualPositionResponseObject](https://docs.dydx.xyz/types/perpetual_position_response_object) ⛁ | The perpetual positions data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/perpetualPositions/parentSubaccountNumber?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art&parentSubaccountNumber=0)
### Get Parent Asset Positions

Query for asset positions (size, buy/sell etc) for a parent subaccount.

#### Method Declaration

Python

```
async def get_parent_subaccount_asset_positions(
    self,
    address: str,
    subaccount_number: int,
    status: Optional[PositionStatus] = None,
    limit: Optional[int] = None,
    created_before_or_at_height: Optional[int] = None,
    created_before_or_at: Optional[str] = None,
) -> Any:
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `parentSubaccountNumber` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | The parent subaccount number of this wallet |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [AssetPositionResponseObject](https://docs.dydx.xyz/types/asset_position_response_object) ⛁ | The asset positions data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The parent subaccount was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/assetPositions/parentSubaccountNumber?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art&parentSubaccountNumber=0)
### Get Parent Transfers

Query for transfers between subaccounts associated with a parent subaccount.

#### Method Declaration

Python

```
async def get_parent_transfers(
    self,
    address: str,
    subaccount_number: int,
    limit: Optional[int] = None,
    created_before_or_at_height: Optional[int] = None,
    created_before_or_at: Optional[str] = None,
) -> Any
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the parent subaccount. |
| `parentSubaccountNumber` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | The identifier for the specific subaccount within the wallet address. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of asset positions to return in the response. |
| `createdBeforeOrAtHeight` | query | [Height](https://docs.dydx.xyz/types/height) | false | Restricts results to positions created at or before a specific blockchain height. |
| `createdBeforeOrAt` | query | [DateTime in UTC](https://docs.dydx.xyz/types/date_time) | false | Restricts results to positions created at or before a specific timestamp (ISO 8601 format). |

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TransferResponseObject](https://docs.dydx.xyz/types/transfer_response_object) ⛁ |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/transfers/parentSubaccountNumber?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art&parentSubaccountNumber=0)
### List Parent Orders

Query for orders filtered by order params of a parent subaccount.

#### Method Declaration

Python

```
async def list_parent_orders(
    self,
    address: str,
    subaccount_number: int,
    limit: Optional[int] = None,
    ticker: Optional[str] = None,
    side: Optional[OrderSide] = None,
    status: Optional[OrderStatus] = None,
    order_type: Optional[OrderType] = None,
    good_til_block_before_or_at: Optional[int] = None,
    good_til_block_time_before_or_at: Optional[str] = None,
    return_latest_orders: Optional[bool] = None,
) -> Any
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `parentSubaccountNumber` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | Parent subaccount number |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of asset positions to return in the response. |
| `ticker` | query | [Ticker](https://docs.dydx.xyz/types/ticker) | false | The ticker filter. |
| `side` | query | [OrderSide](https://docs.dydx.xyz/types/order_side) | false | The order side filter. |
| `status` | query | [OrderStatus](https://docs.dydx.xyz/types/order_status) | false | The order status filter. |
| `type` | query | [OrderType](https://docs.dydx.xyz/types/order_type) | false | The order type filter. |
| `goodTilBlockBeforeOrAt` | query | [Height](https://docs.dydx.xyz/types/height) | false | The block number filter for orders good until before or at. |
| `goodTilBlockTimeBeforeOrAt` | query | [DateTime in UTC](https://docs.dydx.xyz/types/date_time) | false | The timestamp filter for orders good until before or at. |
| `returnLatestOrders` | query | bool | false | Whether to return only the latest orders. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [ListOrdersResponse](https://docs.dydx.xyz/types/list_orders_response) | The orders data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/orders/parentSubaccountNumber?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art&parentSubaccountNumber=0)
### Get Parent Fills

Query for fills (i.e. filled orders data) for a parent subaccount.

#### Method Declaration

Python

```
async def get_parent_fills(
    self,
    address: str,
    subaccount_number: int,
    limit: Optional[int] = None,
    market: Optional[str] = None,
    market_type: Optional[TickerType] = None,
    created_before_or_at_height: Optional[int] = None,
    created_before_or_at: Optional[str] = None,
) -> Any:
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the parent subaccount. |
| `parentSubaccountNumber` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | The identifier for the specific subaccount within the wallet address. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of asset positions to return in the response. |
| `createdBeforeOrAtHeight` | query | [Height](https://docs.dydx.xyz/types/height) | false | Filters results to positions created at or before a specific blockchain height. |
| `market` | query | [Ticker](https://docs.dydx.xyz/types/ticker) | false | Market id like USD-BTC, ETH-USD |
| `marketType` | query | [MarketType](https://docs.dydx.xyz/types/market_type) | false | Market type of filled order Data |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [FillResponseObject](https://docs.dydx.xyz/types/fill_response_object) ⛁ | The fills data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The parent subaccount was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/fills/parentSubaccountNumber?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art&parentSubaccountNumber=0)
### Get Parent Historical Pnl

Query for profit and loss report for the specified time/block range of a parent subaccount.

#### Method Declaration

Python

```
async def get_parent_historical_pnls(
    self,
    address: str,
    subaccount_number: int,
    limit: Optional[int] = None,
    created_before_or_at_height: Optional[int] = None,
    created_before_or_at: Optional[str] = None,
    created_on_or_after_height: Optional[int] = None,
    created_on_or_after: Optional[str] = None,
) -> Any:
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the parent subaccount. |
| `parentSubaccountNumber` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | The identifier for the specific subaccount within the wallet address. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of asset positions to return in the response. |
| `createdBeforeOrAtHeight` | query | [Height](https://docs.dydx.xyz/types/height) | false | Restricts results to positions created at or before a specific blockchain height. |
| `createdBeforeOrAt` | query | [DateTime in UTC](https://docs.dydx.xyz/types/date_time) | false | Restricts results to positions created at or before a specific timestamp (ISO 8601 format). |
| `createdOnOrAfterHeight` | query | [Height](https://docs.dydx.xyz/types/height) | false | Restricts results to positions created on or after a specific blockchain height. |
| `createdOnOrAfter` | query | [DateTime in UTC](https://docs.dydx.xyz/types/date_time) | false | Restricts results to positions created on or after a specific timestamp (ISO 8601 format). |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [PnlTicksResponseObject](https://docs.dydx.xyz/types/pnl_ticks_response_object) ⛁ | The historical PnLs data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The parent subaccount was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/historical-pnl/parentSubaccountNumber?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art&parentSubaccountNumber=0)
### Get Funding Payments

Retrieves funding payment history for a specific subaccount. Funding payments are periodic settlements that occur between long and short positions based on the funding rate.

#### Method Declaration

Python

```
async def get_funding_payments(
    self,
    address: str,
    subaccount_number: int,
    limit: Optional[int] = None,
    ticker: Optional[str] = None,
    after_or_at: Optional[str] = None,
    page: Optional[int] = None,
) -> Any
```

Unification Plan
*   Rename all methods to `get_funding_payments` - shorter is better.
*   Add a `Subaccount` pair to Python and JavaScript, since it's always a pair
*   `page` optional parameter is missing in Python
*   `page` optional parameter is missing in Rust

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `subaccountNumber` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | The identifier for the specific subaccount within the wallet address. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of funding payments to return in the response. |
| `ticker` | query | [Ticker](https://docs.dydx.xyz/types/ticker) | false | The market symbol to filter funding payments by (e.g., "BTC-USD"). If not provided, payments for all markets will be returned. |
| `afterOrAt` | query | [DateTime](https://docs.dydx.xyz/types/date_time) | false | Filters results to funding payments created at or after a specific timestamp (ISO 8601 format). |
| `page` | query | [u32](https://docs.dydx.xyz/types/u32) | false | The page number for paginated results. |

#### Response

A promise that resolves to funding payment data containing details such as payment amount, funding rate, position size, market ticker, and timestamp information.

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [FundingPaymentsResponseObject](https://docs.dydx.xyz/types/funding_payments_response_object) ⛁ | The funding payments data. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/fundingPayments?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art&subaccountNumber=0)
### Get Funding Payments for Parent Subaccount

Retrieves funding payment history for all subaccounts under a parent subaccount. This endpoint aggregates funding payments across all child subaccounts of a given parent subaccount.

#### Method Declaration

Python

```
async def get_funding_payments_for_parent_subaccount(
    self,
    address: str,
    parent_subaccount_number: int,
    limit: Optional[int] = None,
    after_or_at: Optional[str] = None,
    page: Optional[int] = None,
) -> Any
```

Unification Plan
*   Rename all methods to `get_funding_payments_for_parent_subaccount` - shorter is better.
*   Add a `ParentSubaccount` pair to Python and JavaScript, since it's always a pair
*   `page` optional parameter is missing in Python
*   `page` optional parameter is missing in Rust

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `parentSubaccountNumber` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | The identifier for the parent subaccount within the wallet address. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of funding payments to return in the response. |
| `afterOrAt` | query | [DateTime](https://docs.dydx.xyz/types/date_time) | false | Filters results to funding payments created at or after a specific timestamp (ISO 8601 format). |
| `page` | query | [u32](https://docs.dydx.xyz/types/u32) | false | The page number for paginated results. |

#### Response

A promise that resolves to funding payment data containing details such as payment amount, funding rate, position size, market ticker, and timestamp information aggregated across all child subaccounts.

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [FundingPaymentsResponseObject](https://docs.dydx.xyz/types/funding_payments_response_object) ⛁ | The funding payments data. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/fundingPayments/parentSubaccount?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art&parentSubaccountNumber=0)
Markets
-------

TODO: How to access to the `accounts` space.

Python

`market = indexer_client.markets()`

### Get Perpetual Markets

Retrieves perpetual markets.

#### Method Declaration

Python

`def get_perpetual_markets(self, market: str = None) -> Response`

Unification Plan
*   Add alias for the return type in Rust: `PerpetualMarketsMap`

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `market` | query | [Ticker](https://docs.dydx.xyz/types/ticker) | false | The specific market ticker to retrieve. If not provided, all markets are returned. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | Maximum number of asset positions to return in the response. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [PerpetualMarketMap](https://docs.dydx.xyz/types/perpetual_market_map) | The perpetual markets data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The market was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/perpetualMarkets)
### Get Perpetual Market Orderbook

Retrieves the orderbook for a specific perpetual market.

#### Method Declaration

Python

```
async def get_perpetual_market_orderbook(
    self,
    market: str,
) -> dict
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `market` | path | [Ticker](https://docs.dydx.xyz/types/ticker) | true | The market ticker. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [OrderBookResponseObject](https://docs.dydx.xyz/types/order_book_response_object) ⛁ | The orderbook data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The market was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/orderbooks/perpetualMarket/BTC-USD)
### Get Trades

Retrieves trades for a specific perpetual market.

#### Method Declaration

Python

```
async def get_perpetual_market_trades(
    self,
    market: str,
    starting_before_or_at_height: Optional[int] = None,
    limit: Optional[int] = None,
) -> dict
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `market` | path | [Ticker](https://docs.dydx.xyz/types/ticker) | true | The market ticker. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | The maximum number of trades to retrieve. |
| `startingBeforeOrAtHeight` | query | [Height](https://docs.dydx.xyz/types/height) | false | The block height to start retrieving trades from. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TradeResponseObject](https://docs.dydx.xyz/types/trade_response_object) ⛁ | The trades data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The market was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/trades/perpetualMarket/BTC-USD)
### Get Candles

Retrieves candle data for a specific perpetual market.

#### Method Declaration

Python

```
async def get_perpetual_market_candles(
    self,
    market: str,
    resolution: str,
    from_iso: Optional[str] = None,
    to_iso: Optional[str] = None,
    limit: Optional[int] = None,
) -> dict
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `market` | path | [Ticker](https://docs.dydx.xyz/types/ticker) | true | The market ticker. |
| `resolution` | query | [CandleResolution](https://docs.dydx.xyz/types/candle_resolution) | true | The candle resolution (e.g., "1DAY", "1HOUR", "1MIN"). |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | The maximum number of candles to retrieve. |
| `fromIso` | query | [DateTime](https://docs.dydx.xyz/types/date_time) | false | The start timestamp in ISO format. |
| `toIso` | query | [DateTime](https://docs.dydx.xyz/types/date_time) | false | The end timestamp in ISO format. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [CandleResponseObject](https://docs.dydx.xyz/types/candle_response_object) ⛁ | The candle data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/candles/perpetualMarkets/BTC-USD?resolution=1DAY)
### Get Historical Funding

Retrieves historical funding rates for a specific perpetual market.

#### Method Declaration

Python

```
async def get_perpetual_market_historical_funding(
    self,
    market: str,
    effective_before_or_at: Optional[str] = None,
    effective_before_or_at_height: Optional[int] = None,
    limit: Optional[int] = None,
) -> dict
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `market` | path | [Ticker](https://docs.dydx.xyz/types/ticker) | true | The market ticker. |
| `limit` | query | [u32](https://docs.dydx.xyz/types/u32) | false | The maximum number of funding rates to retrieve. |
| `effectiveBeforeOrAt` | query | [DateTime](https://docs.dydx.xyz/types/date_time) | false | The timestamp to retrieve funding rates effective before or at. |
| `effectiveBeforeOrAtHeight` | query | [Height](https://docs.dydx.xyz/types/height) | false | The block height to retrieve funding rates effective before or at. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [HistoricalFundingResponseObject](https://docs.dydx.xyz/types/historical_funding_response_object) ⛁ | The historical funding rates data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The market was not found. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/historicalFunding/BTC-USD)
### Get Sparklines

Retrieves sparkline data for perpetual markets.

#### Method Declaration

Python

```
async def get_perpetual_market_sparklines(
    self,
    period: str = TimePeriod.ONE_DAY
) -> dict
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `timePeriod` | query | [SparklineTimePeriod](https://docs.dydx.xyz/types/sparkline_time_period) | true | The time period for the sparkline data (e.g., "ONE_DAY", "SEVEN_DAYS"). |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [SparklineResponseObject](https://docs.dydx.xyz/types/sparkline_response_object) ⛁ | The sparkline data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/sparklines?timePeriod=ONE_DAY)
Utility
-------

// TODO: Add description

#### Method Declaration

### Get Time

Get current server time of the Indexer.

#### Method Declaration

Python

`async def get_time(self) -> Dict[str, str]`

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TimeResponse](https://docs.dydx.xyz/types/time_response) |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/time)
### Get Height

Current block height and block time (UTC) parsed by the Indexer.

#### Method Declaration

Python

`async def get_height(self) -> Dict[str, str]`

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [HeightResponse](https://docs.dydx.xyz/types/height_response) ⛁ | Dictionary containing the block height and time. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/height)
### Get Screen

Query for screening results (compliance) of the address.

#### Method Declaration

Python

`async def screen(self, address: str) -> Dict[str, bool]:`

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [ComplianceResponse](https://docs.dydx.xyz/types/compliance_response) ⛁ | The compliance data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/screen?address=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art)
### Get Compliance Screen

Screen an address to see if it is restricted.

#### Method Declaration

Python

`async def compliance_screen(self, address: str) -> Any`

Unification Plan
Implement Python and rust method

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| address | Path | string | true | evm or dydx address |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [ComplianceV2Response](https://docs.dydx.xyz/types/compliance_v2_response) | whether the specified address is restricted |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/compliance/screen/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art)
Vaults
------

TODO: How to access to the `vaults` space.

Rust

`let vaults = indexer_client.vaults();`

### Get MegaVault Historical Pnl

MegaVault historical PnL.

#### Method Declaration

Python

`async def get_megavault_historical_pnl(self, resolution)`

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `resolution` | query | [PnlTickInterval](https://docs.dydx.xyz/types/pnl_tick_interval) | true | PnL tick resolution. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [PnlTicksResponseObject](https://docs.dydx.xyz/types/pnl_ticks_response_object) ⛁ | The PnL ticks data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/vault/v1/megavault/historicalPnl?resolution=day)
### Get Vaults Historical Pnl

Vaults historical PnL.

#### Method Declaration

Python

`async def get_vaults_historical_pnl(self, resolution)`

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `resolution` | query | [PnlTickInterval](https://docs.dydx.xyz/types/pnl_tick_interval) | true | PnL tick resolution. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [VaultHistoricalPnl](https://docs.dydx.xyz/types/vault_historical_pnl) ⛁ | The vault historical PnL data. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/vault/v1/megavault/historicalPnl?resolution=day)
### Get MegaVaults Positions

MegaVault positions.

#### Method Declaration

Python

`async def get_megavault_positions(self)`

Unification Plan

#### Parameters

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [VaultPosition](https://docs.dydx.xyz/types/vault_position) ⛁ |
[API Example](https://indexer.v4testnet.dydx.exchange/v4/vault/v1/megavault/positions)
Title: dYdX Documentation

URL Source: https://docs.dydx.xyz/indexer-client/websockets

Published Time: Sun, 19 Oct 2025 18:22:00 GMT

Markdown Content:
The WebSockets API provides data feeds providing the trader real-time information.

See the [guide](https://docs.dydx.xyz/interaction/data/feeds) for examples on how to use the WebSockets API.

Common schemas
--------------

Interactions with the WebSockets endpoint is done using common base JSON schemas for all channels/feed types. For specific feeds, see the following [subsections](https://docs.dydx.xyz/indexer-client/websockets/#feeds).

### Subscribe

Use the following schema to subscribe to a channel.

#### JSON Schema

| Parameter | Type | Description |
| --- | --- | --- |
| `type` | string | Message type (`subscribe`). |
| `channel` | string | Feed type identifier. |
| `id` | string | Selector for channel-specific data. Only used in some channels. |
| `batched` | bool | Reduce incoming messages by batching contents. |

Example

```
{ 
    "type": "subscribe", 
    "channel": "v4_trades",
    "id": "BTC-USD",
    "batched": false
}
```

#### Response

| Parameter | Type | Description |
| --- | --- | --- |
| `type` | string | Message type (`subscribed`). |
| `connection_id` | string | String identifying the subscription. |
| `message_id` | int | Message sequence number sent on the subscription. |
| `id` | string | Selector for channel-specific data. |
| `contents` | value | Channel-specific initial data. |

### Unsubscribe

Use the following schema to unsubscribe from a channel. Similar scheme to the `subscribe` schema, however with the `unsubscribe` type, and without the `batched` field.

#### JSON Schema

| Parameter | Type | Description |
| --- | --- | --- |
| `type` | string | Message type (`unsubscribe`). |
| `channel` | string | Feed type identifier. |
| `id` | string | Selector for channel-specific data. |

Example

```
{
    "type": "unsubscribe",
    "channel": "v4_trades",
    "id": "BTC-USD"
}
```

#### Response

| Parameter | Type | Description |
| --- | --- | --- |
| `type` | string | Message type (`unsubscribed`). |
| `connection_id` | string | String identifying the subscription. |
| `channel` | string | Feed type identifier. |
| `message_id` | int | Message sequence number sent on the subscription. |
| `id` | string | Selector for channel-specific data. Only used in some channels. |

### Data

After subscription, the incoming messages will be serialized using the following schema.

#### JSON Schema

| Parameter | Type | Description |
| --- | --- | --- |
| `connection_id` | string | String identifying the subscription. |
| `channel` | string | Feed type identifier. |
| `id` | string | Selector for channel-specific data. Only used in some channels. |
| `message_id` | int | Message sequence number sent on the subscription. |
| `version` | string | Protocol identifier. |
| `contents` | value | Channel-specific message data. |

Channels
--------

The available clients API is presented below. For each, the subscription and unsubscription functions are shown. Internally, these functions send messages serialized in the [subscribe](https://docs.dydx.xyz/indexer-client/websockets/#json-schema) and [unsubscribe](https://docs.dydx.xyz/indexer-client/websockets/#json-schema-1) JSON schemas above.

For each channel/feed type the sub-schemas employed in the `contents` field of the received [Data](https://docs.dydx.xyz/indexer-client/websockets/#json-schema-2) (after subscription) are shown.

### Subaccounts

Data feed of a subaccount. Data contains updates to the subaccount such as position, orders and fills updates.

#### Method Declaration

Python

```
# class `Subaccounts`
def subscribe(self, address: str, subaccount_number: int) -> Self
def unsubscribe(self, address: str, subaccount_number: int)
```

Unification Plan

#### Schema

The field `id` is a string containing the subaccount ID (address and subaccount number). It is formattted as `{address}/{subaccount-number}`.

The field `contents` is serialized using the following schemas.

##### Messages

| Initial | Update |
| --- | --- |
| [`SubaccountsInitialMessage`](https://docs.dydx.xyz/types/subaccounts_initial_message) | [`SubaccountsUpdateMessage`](https://docs.dydx.xyz/types/subaccounts_update_message)* |

### Markets

Data feed of all dYdX markets. Data contains updates to all markets, including market parameters and oracle prices.

#### Method Declaration

Python

```
# class `Markets`
def subscribe(self, batched: bool = True) -> Self
def unsubscribe(self)
```

Unification Plan

#### Schema

The field `id` is not employed in the subscribe/unsubscribe schemas.

The field `contents` is serialized using the following schemas.

##### Messages

| Initial | Update |
| --- | --- |
| [`MarketsInitialMessage`](https://docs.dydx.xyz/types/markets_initial_message) | [`MarketsUpdateMessage`](https://docs.dydx.xyz/types/markets_update_message)* |

### Trades

Data feed of the trades on a market. Data contains order fills updates, such as the order side, price and size.

#### Method Declaration

Python

```
# class `Trades`
def subscribe(self, market: str, batched: bool = True) -> Self
def unsubscribe(self, market: str)
```

Unification Plan

#### Schema

The field `id` is the market/ticker as a string.

The field `contents` is serialized using the following schemas.

##### Messages

| Initial | Update |
| --- | --- |
| [`TradesInitialMessage`](https://docs.dydx.xyz/types/trades_initial_message) | [`TradesUpdateMessage`](https://docs.dydx.xyz/types/trades_update_message)* |

### Orders

Data feed of the orders of a market. Data contains lists of the bids and asks of the order book.

#### Method Declaration

Python

```
# class `OrderBook`
def subscribe(self, market: str, batched: bool = True) -> Self
def unsubscribe(self, market: str)
```

Unification Plan

#### Schema

The field `id` is the market/ticker as a string.

The field `contents` is serialized using the following schemas.

##### Messages

| Initial | Update |
| --- | --- |
| [`OrdersInitialMessage`](https://docs.dydx.xyz/types/orders_initial_message) | [`OrdersUpdateMessage`](https://docs.dydx.xyz/types/orders_update_message)* |

### Candles

Data feed of the [candles](https://en.wikipedia.org/wiki/Candlestick_chart) of a market. Data contains updates for open, low, high, and close prices, trade volume, for a certain time resolution.

#### Method Declaration

Python

```
# class `Candles`
def subscribe(self, id: str, resolution: CandlesResolution, batched: bool = True) -> Self
def unsubscribe(self, id: str, resolution: CandlesResolution)
```

Unification Plan

#### Schema

The field `id` is a string containing the market and candle resolution. It is formatted as `{market}/{resolution}`.

The field `contents` is serialized using the following schemas.

##### Messages

| Initial | Update |
| --- | --- |
| [`CandlesInitialMessage`](https://docs.dydx.xyz/types/candles_initial_message) | [`CandlesUpdateMessage`](https://docs.dydx.xyz/types/candles_update_message)* |

### Parent Subaccounts

Data feed of a parent subaccount. This channel returns similar data to the [subaccount channel](https://docs.dydx.xyz/indexer-client/websockets/subaccounts).

A parent subaccount is a subaccount numbered between 0 and 127. Used for isolated position management by the dYdX frontend (web).

#### Method Declaration

Python

`# Coming soon.`

Unification Plan

#### Schema

The field `id` is a string containing the subaccount ID (address and subaccount number). It is formattted as `{address}/{subaccount-number}`.

The field `contents` is serialized using the following schemas.

##### Messages

| Initial | Update |
| --- | --- |
| [`ParentSubaccountsInitialMessage`](https://docs.dydx.xyz/types/parent_subaccounts_initial_message) | [`ParentSubaccountsUpdateMessage`](https://docs.dydx.xyz/types/parent_subaccounts_update_message)* |

### Block Height

Data feed of current block height. Data contains the last block height and time.

#### Method Declaration

Python

Unification Plan
*   Add feed to Python, TS clients.

#### Schema

The field `id` is not employed in the subscribe/unsubscribe schemas.

The field `contents` is serialized using the following schemas.

##### Messages

| Initial | Update |
| --- | --- |
| [`BlockHeightInitialMessage`](https://docs.dydx.xyz/types/block_height_initial_message) | [`BlockHeightUpdateMessage`](https://docs.dydx.xyz/types/block_height_update_message)* |
Title: Node API

URL Source: https://docs.dydx.xyz/node-client

Published Time: Tue, 14 Oct 2025 13:34:49 GMT

Warning: This page maybe not yet fully loaded, consider explicitly specify a timeout.
Warning: This page contains shadow DOM that are currently hidden, consider enabling shadow DOM processing.
Warning: This page maybe requiring CAPTCHA, please make sure you are authorized to access this page.

Markdown Content:
Nodes are the servers that manage and maintain the dYdX network. Trading transactions are broadcast to these, which then are evaluated and eventually comitted into state by the underlying consensus mechanim. It serves both a [Private API](https://docs.dydx.xyz/node-client/private), which receives transactions signed by the user, and a [Public API](https://docs.dydx.xyz/node-client/public), available for different data queries. The [Permissioned Keys API](https://docs.dydx.xyz/node-client/authenticators) is also available.

See the [guide](https://docs.dydx.xyz/interaction/endpoints#node-client) on how to use the available Node client to learn how to connect to it.
Title: dYdX Documentation

URL Source: https://docs.dydx.xyz/node-client/private

Published Time: Tue, 14 Oct 2025 11:27:50 GMT

Markdown Content:
Private Node API
----------------

### Place Order

Execute a transaction that places an order on a market. This function takes parameters for wallet authentication, various order details, and optional transaction options to manage specific order types and behaviors.

#### Method Declaration

Python

```
async def place_order(
    self,
    wallet: Wallet,
    order: Order,
    tx_options: Optional[TxOptions] = None,
)
```

Unification Plan
*   Use a convenient `Wallet` and `Order` pair for all clients
*   TypeScript doesn't use authenticators
*   In Python we use them explicitly
*   Consider to do the same like in Rust (set it automatically)

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `wallet` | query | [Wallet](https://docs.dydx.xyz/types/wallet) | true | The wallet to use for signing the transaction. |
| `order` | query | [Order](https://docs.dydx.xyz/types/order) | true | The order to place. |
| `tx_options` | query | [TxOptions](https://docs.dydx.xyz/types/tx_options) | false | Options for transaction to support authenticators. |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TxHash](https://docs.dydx.xyz/types/tx_hash) |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/short_term_order_cancel_example.py#L36) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/main/v4-client-js/examples/short_term_order_composite_example.ts) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/main/v4-client-rs/client/examples/place_order_short_term.rs) | [Guide - Place an order](https://docs.dydx.xyz/interaction/trading#place-an-order)

### Cancel Order

Terminate an existing order using the provided order ID and related parameters, such as block validity periods and transaction options.

#### Method Declaration

Python

```
async def cancel_order(
    self,
    wallet: Wallet,
    order_id: OrderId,
    good_til_block: int = None,
    good_til_block_time: int = None,
    tx_options: Optional[TxOptions] = None,
)
```

Unification Plan
*   Check the `marketId` is really needed (used in `TypeScript`)

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `wallet` | query | [Wallet](https://docs.dydx.xyz/types/wallet) | true | The wallet to use for signing the transaction. |
| `order_id` | query | [OrderId](https://docs.dydx.xyz/types/order_id_obj) | true | The ID of the order to cancel. |
| `good_til_block` | query | [i32](https://docs.dydx.xyz/types/i32) | false | The block number until which the order is valid. Defaults to None. |
| `good_til_block_time` | query | [i32](https://docs.dydx.xyz/types/i32) | false | The block time until which the order is valid. Defaults to None. |
| `tx_options` | query | [TxOptions](https://docs.dydx.xyz/types/tx_options) | false | Options for transaction to support authenticators. |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TxHash](https://docs.dydx.xyz/types/tx_options) | The transaction hash. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The order was not found. |

Examples: [Rust](https://github.com/dydxprotocol/v4-clients/blob/main/v4-client-rs/client/examples/cancel_order.rs) | [Guide - Cancel an order](https://docs.dydx.xyz/interaction/trading#cancel-an-order)

### Batch Cancel Orders

Cancel a batch of short-terms orders.

#### Method Declaration

Python

```
async def batch_cancel_orders(
    self,
    wallet: Wallet,
    subaccount_id: SubaccountId,
    short_term_cancels: List[OrderBatch],
    good_til_block: int,
    tx_options: Optional[TxOptions] = None,
)
```

Unification Plan
*   `TxOptions` is not available in Rust

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `wallet` | query | [Wallet](https://docs.dydx.xyz/types/wallet) | true | The wallet to use for signing the transaction. |
| `subaccount_id` | query | [SubaccountId](https://docs.dydx.xyz/types/subaccount_id) | true | The subaccount ID for which to cancel orders. |
| `short_term_cancels` | query | [OrderBatch](https://docs.dydx.xyz/types/order_batch) ⛁ | true | List of OrderBatch objects containing the orders to cancel. |
| `good_til_block` | query | [Height](https://docs.dydx.xyz/types/height) | true | The last block the short term order cancellations can be executed at. |
| `tx_options` | query | [TxOptions](https://docs.dydx.xyz/types/tx_options) | false | Options for transaction to support authenticators. |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TxHash](https://docs.dydx.xyz/types/tx_hash) |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/main/v4-client-py-v2/examples/batch_cancel_example.py) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/main/v4-client-js/examples/batch_cancel_orders_example.ts) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/main/v4-client-rs/client/examples/batch_cancel_orders.rs)

### Deposit

Deposit funds (USDC) from the address to the subaccount.

#### Method Declaration

Python

```
async def deposit(
    self,
    wallet: Wallet,
    sender: str,
    recipient_subaccount: SubaccountId,
    asset_id: int,
    quantums: int,
)
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `wallet` | query | [Wallet](https://docs.dydx.xyz/types/wallet) | true | The wallet to use for signing the transaction. |
| `sender` | query | string | true | The sender address. |
| `recipient_subaccount` | query | [SubaccountId](https://docs.dydx.xyz/types/Subaccount_id) | true | The recipient subaccount ID. |
| `asset_id` | query | [AssetId](https://docs.dydx.xyz/types/asset_id_node) | true | The asset ID. |
| `quantums` | query | int | true | The amount of quantums to deposit. [See more about quantums](https://docs.dydx.xyz/concepts/trading/quantums#quantums) |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TxHash](https://docs.dydx.xyz/types/tx_hash) |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |

### Withdraw

Withdraw funds (USDC) from the subaccount to the address.

#### Method Declaration

Python

```
async def withdraw(
    self,
    wallet: Wallet,
    sender_subaccount: SubaccountId,
    recipient: str,
    asset_id: int,
    quantums: int,
)
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `wallet` | query | [Wallet](https://docs.dydx.xyz/types/wallet) | true | The wallet to use for signing the transaction. |
| `sender_subaccount` | query | [SubaccountId](https://docs.dydx.xyz/types/subaccount_id) | true | The sender subaccount ID. |
| `recipient` | query | string | true | The recipient subaccount ID. |
| `asset_id` | query | [AssetId](https://docs.dydx.xyz/types/asset_id_node) | true | The asset ID. |
| `quantums` | query | int | true | The amount of quantums to withdraw. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TxHash](https://docs.dydx.xyz/types/tx_hash) | The transaction hash. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/main/v4-client-js/examples/transfer_example_subaccount_transfer.ts) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/main/v4-client-js/examples/transfer_example_withdraw.ts) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/main/v4-client-rs/client/examples/withdraw.rs)

### Transfer

Transfer funds (USDC) between subaccounts.

#### Method Declaration

Python

```
async def transfer(
    self,
    wallet: Wallet,
    sender_subaccount: SubaccountId,
    recipient_subaccount: SubaccountId,
    asset_id: int,
    amount: int,
)
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `wallet` | query | [Wallet](https://docs.dydx.xyz/types/wallet) | true | The wallet to use for signing the transaction. |
| `sender_subaccount` | query | [SubaccountId](https://docs.dydx.xyz/types/subaccount_id) | true | The sender subaccount ID. |
| `recipient_subaccount` | query | [SubaccountId](https://docs.dydx.xyz/types/subaccount_id) | true | The recipient subaccount ID. |
| `asset_id` | query | [AssetId](https://docs.dydx.xyz/types/asset_id_node) | true | The asset ID. |
| `amount` | query | int | true | The amount to transfer i USDC |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TxHash](https://docs.dydx.xyz/types/tx_hash) | The transaction hash. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/main/v4-client-py-v2/examples/transfer_example_transfer.py) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/main/v4-client-js/examples/transfer_example_subaccount_transfer.ts) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/main/v4-client-rs/client/examples/transfer.rs)

### Send Token

Transfer a specified token from one account/address to another.

It requires details such as the wallet for signing the transaction, sender and recipient addresses, and the quantum amount or denomination of the token.

#### Method Declaration

Python

```
async def send_token(
    self,
    wallet: Wallet,
    sender: str,
    recipient: str,
    quantums: int,
    denomination: str,
)
```

Unification Plan
*   All the types are different, revision is needed
*   Standard types like strings are used
*   Broadcast mode?
*   Zero fee?

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `wallet` | query | [Wallet](https://docs.dydx.xyz/types/wallet) | true | The wallet to use for signing the transaction. |
| `sender` | query | String | true | The sender address. |
| `recipient` | query | String | true | The recipient address. |
| `quantums` | query | [i32](https://docs.dydx.xyz/types/i32) | true | The amount of quantums to send. |
| `denomination` | query | [i32](https://docs.dydx.xyz/types/i32) | true | The denomination of the token. |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TxHash](https://docs.dydx.xyz/types/tx_hash) |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Rust](https://github.com/dydxprotocol/v4-clients/blob/main/v4-client-rs/client/examples/send_token.rs)

### Simulate

Pre-execution simulation of a transaction, predicting its execution cost and resource usage without committing any changes.

This method typically returns information like estimated gas fees or other transaction-related metrics to anticipate the impact of operations before they are executed on the blockchain.

#### Method Declaration

Python

`async def simulate(self, transaction: Tx)`

Unification Plan
*   Some extra parameters in TypeScript? What to do with them?

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `transaction` | query | [Tx](https://docs.dydx.xyz/types/tx) | true | The transaction to simulate. |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [GasInfo](https://docs.dydx.xyz/types/gas_info) |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/transfer_example_withdraw_other.py#L20) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/transfer_example_withdraw_other.ts#L37) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/withdraw_other.rs#L52)

### Create Transaction

Create a transaction.

#### Method Declaration

Python

`async def create_transaction(self, wallet: Wallet, message: Message) -> Tx`

Unification Plan

#### Parameters

| Parameter | Location | Type | Mandatory | Description |
| --- | --- | --- | --- | --- |
| `account` | query | [Account](https://docs.dydx.xyz/types/account) | true | Owner's account information |
| `msg` | query | Any | true | Message during create transaction |
| `auth` | query | [Address](https://docs.dydx.xyz/types/address) | false |  |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [tx::Raw](https://docs.dydx.xyz/types/cosmos) |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

### Broadcast Transaction

The `Broadcast Transaction` method is used to send a transaction to the network for processing.

The key parameters include the transaction itself and the mode of broadcasting, which is optional and defaults to synchronous broadcasting mode.

#### Method Declaration

Python

`async def broadcast(self, transaction: Tx, mode=BroadcastMode.BROADCAST_MODE_SYNC)`

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `transaction` | query | [Tx](https://docs.dydx.xyz/types/tx) | true | The transaction to broadcast. |
| `mode` | query | [BroadcastMode](https://docs.dydx.xyz/types/broadcast_mode) | false | The broadcast mode. Defaults to BroadcastMode.BROADCAST_MODE_SYNC. |

:::

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TxHash](https://docs.dydx.xyz/types/tx_hash) |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The transaction was not found. |

Examples: [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/withdraw_other.rs#L71)

### Create Market Permissionless

Create a market permissionless.

#### Method Declaration

Python

```
async def create_market_permissionless(
    self, wallet: Wallet, ticker: str, address: str, subaccount_id: int
) -> Any
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Description |
| --- | --- | --- | --- |
| `account` | query | [Account](https://docs.dydx.xyz/types/account) | Account information |
| `ticker` | query | [Ticker](https://docs.dydx.xyz/types/ticker) | Ticker information |
| `subaccount` | query | [SubaccountInfo](https://docs.dydx.xyz/types/subaccount_info) | Subaccount information |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TxHash](https://docs.dydx.xyz/types/tx_hash) |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |

### Delegate

Delegate tokens from a delegator to a validator.

#### Method Declaration

Python

```
async def delegate(
    self,
    wallet: Wallet,
    delegator: str,
    validator: str,
    quamtums: int,
    denomination: str,
)
```

#### Parameters

| Parameter | Location | Type | Mandatory | Description |
| --- | --- | --- | --- | --- |
| subaccount | query | [SubaccountInfo](https://docs.dydx.xyz/types/subaccount_info) | true | Subaccount number |
| delegator | query | string | true | Delegator information |
| validator | query | string | true | validator information |
| amount | query | string | true | Amount to delegate |
| broadcastMode | query | [BroadcastMode](https://docs.dydx.xyz/types/broadcast_mode) | false | Mode of broadcast |

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [BroadcastTxAsyncResponse](https://docs.dydx.xyz/types/cosmos) |

### Undelegate

Undelegate coins from a delegator to a validator.

#### Method Declaration

Python

```
async def undelegate(
    self,
    wallet: Wallet,
    delegator: str,
    validator: str,
    quamtums: int,
    denomination: str,
)
```

#### Parameters

| Parameter | Location | Type | Mandatory | Description |
| --- | --- | --- | --- | --- |
| subaccount | query | [SubaccountInfo](https://docs.dydx.xyz/types/subaccount_info) | true | Subaccount number |
| delegator | query | string | true | Delegator information |
| validator | query | string | true | validator information |
| amount | query | string | true | Amount to delegate |
| broadcastMode | query | [BroadcastMode](https://docs.dydx.xyz/types/broadcast_mode) | false | Mode of broadcast |

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [BroadcastTxAsyncResponse](https://docs.dydx.xyz/types/cosmos) |

### Register Affiliate

Register affiliate.

#### Method Declaration

Python

```
async def register_affiliate(
    self, wallet: Wallet, referee: str, affiliate: str
) -> Any
```

#### Parameters

| Parameter | Location | Type | Mandatory | Description |
| --- | --- | --- | --- | --- |
| `subaccount` | query | [SubaccountInfo](https://docs.dydx.xyz/types/subaccount_info) | true | Subaccount information |
| `affiliate` | query | string | true | Affiliate information |
| `broadcastMode` | query | [BroadcastMode](https://docs.dydx.xyz/types/broadcast_mode) | false | Mode of broadcast |
| `gasAdjustment` | query | int | false | Gas adjustment value |

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [BroadcastTxAsyncResponse](https://docs.dydx.xyz/types/cosmos) |

### Withdraw Delegator Reward

Withdraw delegator reward.

#### Method Declaration

Python

```
async def withdraw_delegate_reward(
    self, wallet: Wallet, delegator: str, validator: str
) -> Any
```

#### Parameters

| Parameter | Location | Type | Mandatory | Description |
| --- | --- | --- | --- | --- |
| subaccount | query | [SubaccountInfo](https://docs.dydx.xyz/types/subaccount_info) | true | Subaccount number |
| delegator | query | string | true | Delegator information |
| validator | query | string | true | validator information |
| broadcastMode | query | [BroadcastMode](https://docs.dydx.xyz/types/broadcast_mode) | false | Mode of broadcast |

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [BroadcastTxAsyncResponse](https://docs.dydx.xyz/types/cosmos) |

### Close Position

Close position for a given market.

Opposite short-term market orders are used. If provided, the position is only reduced by a size of reduce_by. Note that at the moment dYdX doesn’t support spot trading.

#### Method Declaration

Python

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `account` | query | [Account](https://docs.dydx.xyz/types/account) | true | The wallet address that owns the subaccount. |
| `subaccount` | query | [Subaccount](https://docs.dydx.xyz/types/subaccount) | true | Subaccount to close |
| `market_params` | query | [OrderMarketParams](https://docs.dydx.xyz/types/order_market_params) | true | Market parameters |
| `reduced_by` | query | [BigDecimal](https://docs.dydx.xyz/types/big_decimal) | false |  |
| `client_id` | query | [ClientId](https://docs.dydx.xyz/types/client_id) | true |  |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TxHash](https://docs.dydx.xyz/types/tx_hash) |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |

Examples: [Rust](https://github.com/dydxprotocol/v4-clients/blob/main/v4-client-rs/client/examples/close_position.rs)

### Deposit to MegaVault

Deposit USDC into MegaVault

#### Method Declaration

Python

```
async def deposit(
    self, wallet: Wallet, address: str, subaccount_number: int, amount: Decimal
) -> Any
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Description |
| --- | --- | --- | --- |
| `account` | query | [Account](https://docs.dydx.xyz/types/account) | Owner's account information |
| `subaccount` | query | [SubaccountInfo](https://docs.dydx.xyz/types/subaccount_info) | Subaccount information |
| `amount` | query | Decimal | Amount in usdc to deposit |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TxHash](https://docs.dydx.xyz/types/tx_hash) | The transaction hash. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |

### Withdraw from MegaVault

Withdraw funds (USDC) from the subaccount to the address.

#### Method Declaration

Python

```
async def withdraw(
    self,
    wallet: Wallet,
    address: str,
    subaccount_number: int,
    min_amount: Decimal,
    shares: Optional[int],
) -> Any
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Description |
| --- | --- | --- | --- |
| `account` | query | [Account](https://docs.dydx.xyz/types/account) | Owner's account |
| `subaccount` | query | [SubaccountInfo](https://docs.dydx.xyz/types/subaccount_info) | Subaccount information |
| `min_amount` | query | Decimal | Minimum amount to withdraw i usdc |
| `shares` | query | BigInt | Number of shares |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TxHash](https://docs.dydx.xyz/types/tx_hash) | The transaction hash. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |

### Get Owner Shares in MegaVault

Query the shares associated with an [`Address`].

#### Method Declaration

Python

```
async def get_owner_shares(
    self, address: str
) -> vault_query.QueryMegavaultOwnerSharesResponse
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Description |
| --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | The wallet address that owns the subaccount. |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [QueryMegavaultOwnerSharesResponse](https://docs.dydx.xyz/types/megavault_owner_shares_response) |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

### Get Withdrawal Info of MegaVault

Query the withdrawal information for a specified number of shares.

#### Method Declaration

Python

```
async def get_withdrawal_info(
    self, shares: int
) -> vault_query.QueryMegavaultWithdrawalInfoResponse
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Description |
| --- | --- | --- | --- |
| `shares` | query | BigInt | Number of shares |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [QueryMegavaultWithdrawalInfoResponse](https://docs.dydx.xyz/types/query_megavault_withdrawal_info_response) |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
Title: dYdX Documentation

URL Source: https://docs.dydx.xyz/node-client/public

Published Time: Tue, 21 Oct 2025 21:45:30 GMT

Markdown Content:
Public Node API
---------------

### Get Account Balances

Retrieves the balance for a specific wallet address across all currency denominations within the account. See the [definition](https://github.com/cosmos/cosmos-sdk/tree/main/x/bank#allbalances).

#### Method Declaration

Python

```
async def get_account_balances(
        self,
        address: str,
) -> bank_query.QueryAllBalancesResponse
```

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [Coin](https://docs.dydx.xyz/types/coin) ⛁ | The response containing all account balances. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L20) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/validator_get_example.ts#L17) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L35o) | [API](https://test-dydx-rest.kingnodes.com/cosmos/bank/v1beta1/balances/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art) | [Guide - Get Account Balances](https://docs.dydx.xyz/interaction/data/accounts#get-account-balances)

### Get Account Balance

Retrieves the balance of a specified account address for a particular denomination/token. See the [definition](https://github.com/cosmos/cosmos-sdk/tree/main/x/bank#balance).

#### Method Declaration

Python

```
async def get_account_balance(
    self,
    address: str,
    denom: str,
) -> bank_query.QueryBalanceResponse
```

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `denom` | query | [Denom](https://docs.dydx.xyz/types/denom) | true | Denomination of the token associated with the request. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [Coin](https://docs.dydx.xyz/types/coin) | The account balance. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L28) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L38) | [API](https://test-dydx-rest.kingnodes.com/cosmos/bank/v1beta1/balances/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art/by_denom?denom=adv4tnt) | [Guide - Get Account Balance](https://docs.dydx.xyz/interaction/data/accounts#get-account-balance)

### Get Account

Retrieves an account using its unique wallet address, returning detailed account information encapsulated in the `BaseAccount` structure. See the [definition](https://github.com/cosmos/cosmos-sdk/tree/main/x/auth#account-1).

#### Method Declaration

Python

`async def get_account(self, address: str) -> BaseAccount`

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [BaseAccount](https://docs.dydx.xyz/types/base_account) | The account information. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L12) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/validator_get_example.ts#L9) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L32) | [API](https://test-dydx-rest.kingnodes.com/cosmos/auth/v1beta1/accounts/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art) | [Guide - Get Account](https://docs.dydx.xyz/interaction/data/accounts#get-account)

### Get Latest Block

Retrieves the most recent block from the blockchain network. This is useful for obtaining the latest state or data committed on the chain, ensuring the application operates with up-to-date information.

#### Method Declaration

Python

`async def latest_block(self) -> tendermint_query.GetLatestBlockResponse`

#### Parameters

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [Block](https://docs.dydx.xyz/types/block) | The latest block. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L36) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L53) | [API](https://test-dydx-rest.kingnodes.com/cosmos/base/tendermint/v1beta1/blocks/latest)| [Guide - Get Latest Block](https://docs.dydx.xyz/interaction/data/market#get-latest-block-height)

### Get Latest Block Height

Retrieves the most recent block height from a blockchain network. Internally it uses the [`Get Latest Block`](https://docs.dydx.xyz/node-client/public/#get-latest-block) API call.

#### Method Declaration

Python

`async def latest_block_height(self) -> int`

#### Parameters

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [Height](https://docs.dydx.xyz/types/height) | The latest block height. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L44) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L56)

### Get User Stats

Retrieves statistical data for a user's Maker and Taker positions associated with a specified wallet address.

#### Method Declaration

Python

```
async def get_user_stats(
    self,
    address: str,
) -> stats_query.QueryUserStatsResponse
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `user` | query | [Address](https://docs.dydx.xyz/types/Address) | true | The wallet address that owns the account. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [UserStats](https://docs.dydx.xyz/types/user_stats) | The response containing the user stats. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L52) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/validator_get_example.ts#L81) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L59) | [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/v4/stats/user_stats?user=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art)

### Get All Validators

Fetches a list of all validators, optionally filtering them by a specified status. See the [definition](https://github.com/cosmos/cosmos-sdk/tree/main/x/staking#validators-2).

#### Method Declaration

Python

```
async def get_all_validators(
    self,
    status: str = "",
) -> staking_query.QueryValidatorsResponse
```

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `status` | query | string | false | Status to filter out the matched result. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [Validator](https://docs.dydx.xyz/types/validator) ⛁ | The response containing all validators. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L60) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/validator_get_example.ts#L131) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L62) | [API](https://test-dydx-rest.kingnodes.com/cosmos/staking/v1beta1/validators)

### Get Subaccounts

Retrieves a comprehensive list of all subaccounts, returning structured information encapsulated in a response object.

#### Method Declaration

Python

`async def get_subaccounts(self) -> QuerySubaccountAllResponse`

#### Parameters

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [SubaccountInfo](https://docs.dydx.xyz/types/subaccount_info) ⛁ |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L77) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/validator_get_example.ts#L25) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L68) | [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/subaccounts/subaccount) | [Guide - Get Subaccounts](https://docs.dydx.xyz/interaction/data/accounts#get-account-subaccounts)

### Get Subaccount

Fetches details of a specific subaccount based on its owner's address and the subaccount's unique number.

#### Method Declaration

Python

```
async def get_subaccount(
    self,
    address: str,
    account_number: int,
) -> Optional[subaccount_type.Subaccount]
```

Unification Plan
*   Rust uses `Subaccount` - a wrapper that combines `Address` with `SubaccountNumber`, it's safer to create the same type for Python and TypeScript

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `owner` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `number` | query | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | The identifier for the specific subaccount withing the wallet address. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [SubaccountInfo](https://docs.dydx.xyz/types/subaccount_info) | The response containing the subaccount. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L68) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/validator_get_example.ts#L33) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L65) | [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/subaccounts/subaccount/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art/0) | [Guide - Get Subaccount](https://docs.dydx.xyz/interaction/data/accounts#get-account-subaccount)

### Get Clob Pair

Fetches the order book pair identified by a given ID, allowing users to retrieve detailed information about a specific trading pair within a Central Limit Order Book (CLOB) system.

The response includes data structured within the `ClobPair` schema.

#### Method Declaration

Python

`async def get_clob_pair(self, pair_id: int) -> clob_pair_type.ClobPair`

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `id` | query | [u32](https://docs.dydx.xyz/types/u32) | true | Clob pair ID |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [ClobPair](https://docs.dydx.xyz/types/clob_pair) | The clob pair information. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The clob pair was not found. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L86) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L71) | [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/clob/clob_pair/1)

### Get Clob Pairs

Obtain a comprehensive list of all available order book trading pairs.

#### Method Declaration

Python

`async def get_clob_pairs(self) -> QueryClobPairAllResponse`

Unification Plan
*   Python and TypeScript don't contain options

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `pagination` | query | [PageRequest](https://docs.dydx.xyz/types/page_request) | false | Parameters of pagination. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [ClobPair](https://docs.dydx.xyz/types/clob_pair) ⛁ | The response containing all clob pairs. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L94) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/validator_get_example.ts#L49) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L74) | [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/clob/clob_pair)

### Get Price

Retrieve the current market price for a specified market, identified by its market ID.

#### Method Declaration

Python

`async def get_price(self, market_id: int) -> market_price_type.MarketPrice`

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `market_id` | query | [u32](https://docs.dydx.xyz/types/u32) | true | ID of the market to fetch price of |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [MarketPrice](https://docs.dydx.xyz/types/market_price) |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The market was not found. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L102) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L102) | [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/prices/market/1)

### Get Prices

Query all market prices from the system, providing an overview of current market values.

#### Method Declaration

Python

`async def get_prices(self) -> QueryAllMarketPricesResponse`

Unification Plan
*   Python and TypeScript don't contain options

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `pagination` | query | [PageRequest](https://docs.dydx.xyz/types/page_request) | false | Parameters of pagination. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [MarketPrice](https://docs.dydx.xyz/types/market_price) ⛁ | The response containing all market prices. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L110) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/validator_get_example.ts#L57) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L80) | [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/prices/market)

### Get Perpetual

Queries a specific perpetual contract by its unique perpetual ID, returning details about the contract.

#### Method Declaration

Python

`async def get_perpetual(self, perpetual_id: int) -> QueryPerpetualResponse`

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `id` | query | [u32](https://docs.dydx.xyz/types/u32) | true | Perpetual ID |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [Perpetual](https://docs.dydx.xyz/types/perpetual) |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The perpetual was not found. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L118) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L83) | [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/perpetuals/perpetual/1)

### Get Perpetuals

Retrieve a list of all perpetuals currently available in the system.

#### Method Declaration

Python

`async def get_perpetuals(self) -> QueryAllPerpetualsResponse`

Unification Plan
*   Python and TypeScript don't contain options
*   Options in protocol are not optional

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `pagination` | query | [PageRequest](https://docs.dydx.xyz/types/page_request) | false | Parameters of pagination. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [Perpetual](https://docs.dydx.xyz/types/perpetual) ⛁ | The response containing all perpetuals. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L126) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L86) | [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/perpetuals/perpetual)

### Get Equity Tier Limit Config

Fetch the configuration details that outline the limits set for different tiers of equity.

#### Method Declaration

Python

```
async def get_equity_tier_limit_config(
    self,
) -> equity_tier_limit_config_type.EquityTierLimitConfiguration:
```

Unification Plan

#### Parameters

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [EquityTierLimitConfiguration](https://docs.dydx.xyz/types/equity_tier_limit_configuration) |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L134) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/validator_get_example.ts#L89) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L89) | [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/clob/equity_tier)

### Get Delegator Delegations

Retrieves all delegations associated with a specific delegator address. See the [definition](https://github.com/cosmos/cosmos-sdk/tree/main/x/staking#delegatordelegations).

#### Method Declaration

Python

```
async def get_delegator_delegations(
    self, delegator_addr: str
) -> staking_query.QueryDelegatorDelegationsResponse
```

Unification Plan
*   Python and TypeScript don't contain options
*   Options in protocol are not optional
*   Two types of options (v4 and cosmos, are the same, please use cosmos)

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `delegator_addr` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `pagination` | query | [PageRequest](https://docs.dydx.xyz/types/page_request) | false | Parameters of pagination. |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [DelegationResponse](https://docs.dydx.xyz/types/delegation_response) ⛁ |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L142) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/validator_get_example.ts#L105) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L92) | [API](https://test-dydx-rest.kingnodes.com/cosmos/staking/v1beta1/delegations/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art)

### Get Delegator Unbonding Delegations

Query all unbonding delegations associated with a specific delegator address. See the [definition](https://github.com/cosmos/cosmos-sdk/tree/main/x/staking#delegatorunbondingdelegations).

#### Method Declaration

Python

```
async def get_delegator_unbonding_delegations(
    self, delegator_addr: str
) -> staking_query.QueryDelegatorUnbondingDelegationsResponse
```

Unification Plan
*   Python and TypeScript don't contain options
*   Options in protocol are not optional
*   Two types of options (v4 and cosmos, are the same, please use cosmos)

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `delegator_addr` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `pagination` | query | [PageRequest](https://docs.dydx.xyz/types/page_request) | false | Parameters of pagination. |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [UnbondingDelegation](https://docs.dydx.xyz/types/unbonding_delegations) ⛁ |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L150) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/validator_get_example.ts#L113) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L98) | [API](https://test-dydx-rest.kingnodes.com/cosmos/staking/v1beta1/delegators/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art/unbonding_delegations)

### Get Delayed Complete Bridge Messages

Retrieve delayed bridge messages associated with a specified wallet address, focusing on messages that have not yet reached completion.

It requires the address of the wallet to access its related subaccount messages and returns a structured response detailing the delayed messages.

#### Method Declaration

Python

```
async def get_delayed_complete_bridge_messages(
    self,
    address: str = "",
) -> bridge_query.QueryDelayedCompleteBridgeMessagesResponse
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [DelayedCompleteBridgeMessage](https://docs.dydx.xyz/types/delayed_complete_bridge_messages) ⛁ |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L160) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/validator_get_example.ts#L139) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L104) | [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/v4/bridge/delayed_complete_bridge_messages)

### Get Fee Tiers

Retrieves current fee tiers associated with perpetual trading, helping to understand the fees applied based on trading volume or other criteria.

#### Method Declaration

Python

`async def get_fee_tiers(self) -> fee_tier_query.QueryPerpetualFeeParamsResponse`

Unification Plan

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [PerpetualFeeTier](https://docs.dydx.xyz/types/perpetual_fee_tier) ⛁ |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L168) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/validator_get_example.ts#L65) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L110) | [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/v4/feetiers/perpetual_fee_params)

### Get User Fee Tier

Retrieves the perpetual fee tier associated with a specific wallet address, providing information on the user's current fee structure.

#### Method Declaration

Python

```
async def get_user_fee_tier(
    self, address: str
) -> fee_tier_query.QueryUserFeeTierResponse
```

Unification Plan

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `user` | query | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [PerpetualFeeTier](https://docs.dydx.xyz/types/perpetual_fee_tier) | The response containing the user fee tier. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L176) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/validator_get_example.ts#L73) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L113) | [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/v4/feetiers/user_fee_tier?user=dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art)| [Guide - Get User Fee Tier](https://docs.dydx.xyz/interaction/data/market#get-user-fee-tier)

### Get Rewards Params

Retrieves the parameters for the rewards system, providing insight into the set configurations for earning and distributing rewards.

#### Method Declaration

Python

`async def get_rewards_params(self) -> rewards_query.QueryParamsResponse`

Unification Plan
*   Rename `Params` to `RewardsParams` in Rust

#### Parameters

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [RewardsParams](https://docs.dydx.xyz/types/rewards_params) |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/validator_get_example.py#L184) | [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/validator_get_example.ts#L97) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L116) | [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/v4/rewards/params) | [Guide - Get Rewards Params](https://docs.dydx.xyz/interaction/data/market#get-rewards-params)

### Get Affiliate Info

Get affiliate info by address.

#### Method Declaration

Python

```
async def get_affiliate_info(
    self, address: str
) -> affiliate_query.AffiliateInfoResponse
```

#### Parameters

| Parameter | Location | Type | Mandatory | Description |
| --- | --- | --- | --- | --- |
| `address` | Query | [Address](https://docs.dydx.xyz/types/address) | true | Address to get affiliate info |

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [AffiliateModule.AffiliateInfoResponse](https://docs.dydx.xyz/types/cosmos) |

Examples: [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/affiliates/affiliate_info/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art)

### Get Affiliate White List

Get affiliate white list.

#### Method Declaration

Python

```
async def get_affiliate_whitelist(
    self,
) -> affiliate_query.AffiliateWhitelistResponse
```

#### Parameters

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [AffiliateModule.AffiliateWhitelistResponse](https://docs.dydx.xyz/types/cosmos) |

Examples: [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/affiliates/affiliate_whitelist)

### Get All Affiliate Tiers

Get all affiliate tiers.

#### Method Declaration

Python

```
async def get_all_affiliate_tiers(
    self,
) -> affiliate_query.AllAffiliateTiersResponse
```

#### Parameters

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [AffiliateModule.AllAffiliateTiersResponse](https://docs.dydx.xyz/types/cosmos) |

Examples: [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/affiliates/all_affiliate_tiers)

### Get All Gov Proposals

Get all gov proposals.

#### Method Declaration

Python

```
async def get_all_gov_proposals(
    self,
    proposal_status: Optional[str] = None,
    voter: Optional[str] = None,
    depositor: Optional[str] = None,
    key: Optional[bytes] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    count_total: Optional[bool] = False,
    reverse: Optional[bool] = False,
) -> gov_query.QueryProposalsResponse
```

#### Parameters

| Parameter | Location | Type | Mandatory | Description |
| --- | --- | --- | --- | --- |
| proposalStatus | Query | [ProposalStatus](https://docs.dydx.xyz/types/cosmos) | true | Status of the proposal to filter by. |
| voter | Query | string | false | Voter to filter by |
| depositor | Query | string | false | Depositor to filter by. |

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [GovV1Module.QueryProposalsResponse](https://docs.dydx.xyz/types/cosmos) |

Examples: [API](https://test-dydx-rest.kingnodes.com/cosmos/gov/v1/proposals?proposalStatus=0)

### GetDelegationTotalRewards

Get all unbonding delegations from a delegator.

#### Method Declaration

Python

```
async def get_delegation_total_rewards(
      self, address: str
  ) -> distribution_query.QueryDelegationTotalRewardsResponse
```

Implement Python and Rust method

#### Parameters

| Parameter | Location | Type | Mandatory | Description |
| --- | --- | --- | --- | --- |
| delegatorAddress | Query | string | true | Address of the delegator |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [DistributionModule.QueryDelegationTotalRewardsResponse](https://docs.dydx.xyz/types/cosmos) | All unbonding delegations from a delegator. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [API](https://test-dydx-rest.kingnodes.com/cosmos/distribution/v1beta1/delegators/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art/rewards)

### Get Node Info

Query for node info.

#### Method Declaration

Python

`async def get_node_info(self) -> tendermint_query.GetNodeInfoResponse`

Unification Plan

#### Parameters

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [GetNodeInfoResponse](https://docs.dydx.xyz/types/get_node_info_response) |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/validator_get.rs#L44) | [API](https://test-dydx-rest.kingnodes.com/cosmos/base/tendermint/v1beta1/node_info)

### Get Referred By

Get referred by.

#### Method Declaration

Python

`async def get_referred_by(self, address: str) -> affiliate_query.ReferredByResponse`

#### Parameters

| Parameter | Location | Type | Mandatory | Description |
| --- | --- | --- | --- | --- |
| `address` | Query | [Address](https://docs.dydx.xyz/types/address) | true | Address to get referred by |

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [AffiliateModule.ReferredByResponse](https://docs.dydx.xyz/types/cosmos) |

Examples: [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/affiliates/referred_by/dydx14zzueazeh0hj67cghhf9jypslcf9sh2n5k6art)

### Get Withdrawal and Transfer Gating Status

Get withdrawal and transfer gating status.

#### Method Declaration

Python

```
async def get_withdrawal_and_transfer_gating_status(
    self, perpetual_id: int
) -> subaccount_query.QueryGetWithdrawalAndTransfersBlockedInfoResponse
```

#### Parameters

| Parameter | Location | Type | Mandatory | Description |
| --- | --- | --- | --- | --- |
| perpetualId | Query | int | true | Perpetual id |

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [SubaccountsModule.QueryGetWithdrawalAndTransfersBlockedInfoResponse](https://docs.dydx.xyz/types/cosmos) |

Examples: [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/subaccounts/withdrawals_and_transfers_blocked_info/1)

### Get Withdrawal Capacity By Denom

Get withdrawal capacity by denom.

#### Method Declaration

Python

```
async def get_withdrawal_capacity_by_denom(
    self, denom: str
) -> rate_query.QueryCapacityByDenomResponse
```

#### Parameters

| Parameter | Location | Type | Mandatory | Description |
| --- | --- | --- | --- | --- |
| denom | Query | string | true | Denomination value |

#### Response

| Status | Meaning | Schema |
| --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [RateLimitModule.QueryCapacityByDenomResponse](https://docs.dydx.xyz/types/cosmos) |

Examples: [API](https://test-dydx-rest.kingnodes.com/dydxprotocol/v4/ratelimit/capacity_by_denom?denom=adv4tnt)

### Query Address

Fetch account’s number and sequence number from the network.

#### Method Declaration

Python

`async def query_address(self, address: str) -> (int, int)`

Unification Plan

#### Parameters

| Parameter | Location | Type | Description |
| --- | --- | --- | --- |
| `address` | query | [Address](https://docs.dydx.xyz/types/address) | The wallet address that owns the account. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | Pair of ([u64], [u64]) | The response containing the account. |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

### Get Order Router Revenue share

Retrieves order router revenue share

#### Method Declaration

Python

`async def get_order_router_revenue_share(self, address: str) -> QueryOrderRouterRevShareResponse`

#### Parameters

| Parameter | Location | Type | Mandatory | Description |
| --- | --- | --- | --- | --- |
| address | Query | string | true | Address of the revenue share recipient |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [QueryOrderRouterRevShareResponse](https://docs.dydx.xyz/types/query_order_router_revenue_share_response) | Order router revenue share |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/95f2ad4b7d87e2c8f819138fcbe903826af47230/v4-client-py-v2/examples/revenue_share_example.py)

### Get Market Mapper Revenue Share Details

Retrieves market mapper revenue share details

#### Method Declaration

Python

`async def get_market_mapper_revenue_share_details(self, market_id: int) -> QueryMarketMapperRevShareDetailsResponse`

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `market_id` | query | int | true | Market id |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [QueryMarketMapperRevShareDetailsResponse](https://docs.dydx.xyz/types/query_market_mapper_revenue_share_details_response) | Market mapper revenue share details |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/95f2ad4b7d87e2c8f819138fcbe903826af47230/v4-client-py-v2/examples/revenue_share_example.py)

### Get Market Mapper Revenue Share Parmas

Retrieves market mapper revenue share params

#### Method Declaration

Python

`async def get_market_mapper_revenue_share_param(self) -> QueryMarketMapperRevenueShareParamsResponse`

#### Parameters

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [QueryMarketMapperRevenueShareParamsResponse](https://docs.dydx.xyz/types/query_market_mapper_revenue_share_params_response) | Market mapper revenue share params |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/95f2ad4b7d87e2c8f819138fcbe903826af47230/v4-client-py-v2/examples/revenue_share_example.py)

### Get Unconditional Revenue Sharing Config

Retrieves unconditional revenue share config

#### Method Declaration

Python

`async def get_unconditional_revenue_sharing_config(self) -> QueryUnconditionalRevShareConfigResponse`

#### Parameters

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [QueryUnconditionalRevShareConfigResponse](https://docs.dydx.xyz/types/query_unconditional_revenue_share_config_response) | Unconditional revenue share config |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/95f2ad4b7d87e2c8f819138fcbe903826af47230/v4-client-py-v2/examples/revenue_share_example.py)
Title: dYdX Documentation

URL Source: https://docs.dydx.xyz/noble-client

Published Time: Tue, 21 Oct 2025 18:46:21 GMT

Markdown Content:
Methods
-------

### Connect

Connect the Noble client to the Noble network.

#### Method Declaration

Python

`async def connect(self, mnemonic: str)`

#### Parameters

#### Response

Examples: [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/noble_example.ts#L19) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/wallet.rs#L89)

### Get Account Balance

Query token balance of an account/address.

#### Method Declaration

Python

```
async def get_account_balance(
    self, address: str, denom: str
) -> bank_query.QueryBalanceResponse
```

#### Parameters

#### Response

Examples: [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/noble_example.ts#L93)

### Get Account Balances

Query all balances of an account/address.

#### Method Declaration

Python

```
async def get_account_balances(
    self, address: str
) -> bank_query.QueryAllBalancesResponse:
```

#### Parameters

#### Response

Examples: [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/noble_example.ts#L58) | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/noble_transfer.rs#L62)

### Get account

Query for [an account](https://github.com/cosmos/cosmos-sdk/tree/main/x/auth#account-1) by it's address.

#### Method Declaration

Python

`async def get_account(self, address: str) -> BaseAccount`

#### Parameters

#### Response

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/basic_adder.py#L159) | [TypeScript] | [Rust](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-rs/client/examples/wallet.rs#L89)

### Query Address

Fetch account's number and sequence number from the network.

#### Method Declaration

Python

`async def query_address(self, address: str) -> (int, int)`

#### Parameters

#### Response

### Send Token Ibc

Transfer a token asset between Cosmos blockchain networks.

#### Method Declaration

Python

Unification Plan
*   Generalize to all IBC/blockchains.
*   Missing in Python.
*   Missing in TS: user required to produce the low-level message and then `post.send()` it.

#### Parameters

| Parameter | Location | Type | Mandatory | Description |
| --- | --- | --- | --- | --- |
| `account` | query | [Account](https://docs.dydx.xyz/types/account) | true | The account. |
| `sender` | query | [Address](https://docs.dydx.xyz/types/address) | true | Address of the sender. |
| `recipient` | query | [Address](https://docs.dydx.xyz/types/address) | true | Address of the recipient. |
| `token` | query | int | true | Token type and amount to transfer. |
| `source_channel` | query | String | true | Source IBC relay channel. |

#### Response

| Status | Meaning | Schema |  |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) | [TxHash] |  |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid. |

### Simulate

#### Method Declaration

Python

```
async def simulate_transaction(
    self,
    messages: List[dict],
    gas_price: str = "0.025uusdc",
    memo: Optional[str] = None,
) -> Fee:
```

#### Parameters

#### Response

Examples: [TypeScript](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-js/examples/noble_example.ts#L78)
Title: dYdX Documentation

URL Source: https://docs.dydx.xyz/faucet-client

Published Time: Thu, 16 Oct 2025 10:14:34 GMT

Markdown Content:
Faucet API
----------

Methods
-------

### Fill

Add testnet USDC to a subaccount.

#### Method Declaration

Python

```
async def fill(
    self,
    address: str,
    subaccount_number: int,
    amount: float,
    headers: Optional[Dict] = None,
) -> httpx.Response
```

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | body | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |
| `subaccount_number` | body | [SubaccountNumber](https://docs.dydx.xyz/types/subaccount_number) | true | A number that identifies a certain subaccount of the address |
| `amount` | body | [BigDecimal](https://docs.dydx.xyz/types/big_decimal) | true | Amount to fill |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) |  | The response |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid |
| `404` | [Not Found](https://docs.dydx.xyz/types/not-found) |  | The subaccount was not found. |

### Fill Native

Add native dYdX testnet token to an address.

#### Method Declaration

Python

```
async def fill_native(
    self,
    address: str,
    headers: Optional[Dict] = None,
) -> httpx.Response
```

#### Parameters

| Parameter | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `address` | body | [Address](https://docs.dydx.xyz/types/address) | true | The wallet address that owns the account. |

#### Response

| Status | Meaning | Schema | Description |
| --- | --- | --- | --- |
| `200` | [OK](https://docs.dydx.xyz/types/ok) |  | The response |
| `400` | [Bad Request](https://docs.dydx.xyz/types/bad-request) |  | The request was malformed or invalid |

Examples: [Python](https://github.com/dydxprotocol/v4-clients/blob/3e8c7e1b960291b7ef273962d374d9934a5c4d33/v4-client-py-v2/examples/fund_account_example.py#L25)
Title: Open Source Repositories

URL Source: https://docs.dydx.xyz/repositories

Markdown Content:
Please find the open source repositories on our [GitHub](https://github.com/dydxprotocol):

*   [Monorepo](https://github.com/dydxprotocol/v4-chain)
    *   [Protocol](https://github.com/dydxprotocol/v4-chain/tree/main/protocol)
    *   [Indexer](https://github.com/dydxprotocol/v4-chain/tree/main/indexer)

*   [Clients](https://github.com/dydxprotocol/v4-clients)
*   [Frontend](https://github.com/dydxprotocol/v4-web)
*   [iOS](https://github.com/dydxprotocol/v4-native-ios)
*   [Android](https://github.com/dydxprotocol/v4-native-android)
*   [Terraform](https://github.com/dydxprotocol/v4-infrastructure)
*   [dYdX Technical Docs](https://github.com/dydxprotocol/v4-documentation)
*   [Pocket protector TG bot docs](https://docs.pocketprotector.xyz/)

When contributing, please ensure your commits are verified. You can follow these steps to do so:

*   [Generate a new signing key](https://docs.github.com/en/authentication/managing-commit-signature-verification/generating-a-new-gpg-key) for work use and [turn on Vigilant Mode](https://docs.github.com/en/authentication/managing-commit-signature-verification/displaying-verification-statuses-for-all-of-your-commits)
*   [Tell Git about your GPG key](https://docs.github.com/en/authentication/managing-commit-signature-verification/telling-git-about-your-signing-key) and install `pinentry` if necessary
