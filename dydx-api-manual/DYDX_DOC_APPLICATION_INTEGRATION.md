Title: Integration Guide

URL Source: https://docs.dydx.xyz/interaction/integration/integration

Published Time: Tue, 14 Oct 2025 13:32:59 GMT

Markdown Content:
This guide outlines the development of a perpetual trading front-end application using the dYdX v4 application chain APIs. It covers backend data interpretation and rendering for end users, as well as trade execution. While maintaining a high-level perspective, it addresses specific details as needed. For in-depth implementation details, refer to the dYdX source repository, where dYdX Trading Inc. maintains the trading application's source code for web, iOS, and Android platforms.

Overview of dYdX Repositories
-----------------------------

The following repos contain the source code for the dYdX client applications. They can serve as a good reference if you are wondering about the implementation details:

Main applications
-----------------

### [v4-web](https://github.com/dydxprotocol/v4-web).

The web application. This is the React application that powers the [https://dydx.trade](https://dydx.trade/) site. It references the v4-client-js repo for read/write data from the validator.

### [v4-native-ios](https://github.com/dydxprotocol/v4-native-ios).

The iOS application written in Swift It’s powered by the abacus library for its core trading logic. It also uses the v4-client-js for read/write data from the validator, and the cartera-ios library to interact with mobile wallet apps.

### [v4-native-android](https://github.com/dydxprotocol/v4-native-android).

The Android application written in Kotlin. Same with the iOS app, it uses abacus at its core, and use the v4-client-js for read/write data from the validator. Cartera-android is used to interact with mobile wallet apps.

Support libraries
-----------------

### [v4-client-js](https://github.com/dydxprotocol/v4-clients/tree/main/v4-client-js).

Typescript library that wraps the common functions to query and write to the validator/blockchain. It takes a user’s mnemonic and then can send transactions to the validator on the user's behalf. It’s responsible for all data directly flowing in between the client applications and the validator.

### [abacus](https://github.com/dydxprotocol/v4-abacus).

Kotlin library that powers the core trading logic of the iOS and Android applications. The library pulls the data from the indexer and executes transactions by calling v4-client-js.

### [v4-localization](https://github.com/dydxprotocol/v4-localization).

Contains localization data used by all client applications. There is no application logic.
Title: Data sources

URL Source: https://docs.dydx.xyz/interaction/integration/integration-data

Markdown Content:
Data sources – dYdX Documentation

===============

[Skip to content](https://docs.dydx.xyz/interaction/integration/integration-data#vocs-content)

[![Image 1: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Guide

Getting Started

[Preparing to Trade](https://docs.dydx.xyz/interaction/endpoints)[Wallet Setup](https://docs.dydx.xyz/interaction/wallet-setup)[Trading](https://docs.dydx.xyz/interaction/trading)

Trading Data

[Permissioned Keys](https://docs.dydx.xyz/interaction/permissioned-keys)

Deposits & Withdrawals

Application Integration

[Overview](https://docs.dydx.xyz/interaction/integration/integration)[Data Sources](https://docs.dydx.xyz/interaction/integration/integration-data)[Compliance](https://docs.dydx.xyz/interaction/integration/integration-compliance)[Onboarding](https://docs.dydx.xyz/interaction/integration/integration-onboarding)[Markets](https://docs.dydx.xyz/interaction/integration/integration-markets)[User portfolio](https://docs.dydx.xyz/interaction/integration/integration-portfolio)[Placing a trade](https://docs.dydx.xyz/interaction/integration/integration-trade)[Builder codes](https://docs.dydx.xyz/interaction/integration/integration-builder-codes)[Revnue Share](https://docs.dydx.xyz/interaction/integration/integration-revshare)

API

Concepts

Nodes

Policies

Search...

[![Image 2: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

[![Image 3: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Menu

Data Sources

On this page

[Ask in ChatGPT](https://chatgpt.com/?hints=search&q=Please%20research%20and%20analyze%20this%20page%3A%20https%3A%2F%2Fdocs.dydx.xyz%2Finteraction%2Fintegration%2Fintegration-data%20so%20I%20can%20ask%20you%20questions%20about%20it.%20Once%20you%20have%20read%20it%2C%20prompt%20me%20with%20any%20questions%20I%20have.%20Do%20not%20post%20content%20from%20the%20page%20in%20your%20response.%20Any%20of%20my%20follow%20up%20questions%20must%20reference%20the%20site%20I%20gave%20you.)

On this page
------------

*   [Data sources](https://docs.dydx.xyz/interaction/integration/integration-data#data-sources-1)

    *   [Indexer](https://docs.dydx.xyz/interaction/integration/integration-data#indexer)
    *   [Node Client](https://docs.dydx.xyz/interaction/integration/integration-data#node-client)
    *   [Metadata Service](https://docs.dydx.xyz/interaction/integration/integration-data#metadata-service)

    

Data sources[](https://docs.dydx.xyz/interaction/integration/integration-data#data-sources)
===========================================================================================

The client application would need the obtain the data from the following sources:

Data sources[](https://docs.dydx.xyz/interaction/integration/integration-data#data-sources-1)
---------------------------------------------------------------------------------------------

### [Indexer](https://docs.dydx.xyz/indexer-client)[](https://docs.dydx.xyz/interaction/integration/integration-data#indexer)

The Indexer aggregates blockchain data to provide a Web2 interface for client applications. Clients access updated market data, order books, and user account information through REST and WebSocket endpoints. All data from the Indexer is read-only.

### [Node Client](https://docs.dydx.xyz/node-client)[](https://docs.dydx.xyz/interaction/integration/integration-data#node-client)

The client application submits transactions to the blockchain through the validator and also reads data from it. It uses v4-client-js functions to streamline read and write operations.

### Metadata Service[](https://docs.dydx.xyz/interaction/integration/integration-data#metadata-service)

Static market data, including market icons, names, and various URLs, can be retrieved from this REST service. There are two endpoints (use POST instead of GET):

*   `metadata-service/v1/info`: Returns a list of market metadata:

`curl --request POST 'https://66iv2m87ol.execute-api.ap-northeast-1.amazonaws.com/mainnet/metadata-service/v1/info`

*   `metadata-service/v1/prices`: Returns a list of spot market pricing information. Sample curl request:

`curl --request POST 'https://66iv2m87ol.execute-api.ap-northeast-1.amazonaws.com/mainnet/metadata-service/v1/prices'`

Last updated: 9/19/25, 5:57 AM

[Overview Previous shift←](https://docs.dydx.xyz/interaction/integration/integration)[Compliance Next shift→](https://docs.dydx.xyz/interaction/integration/integration-compliance)
Title: Compliance

URL Source: https://docs.dydx.xyz/interaction/integration/integration-compliance

Published Time: Tue, 21 Oct 2025 13:40:10 GMT

Markdown Content:
[Skip to content](https://docs.dydx.xyz/interaction/integration/integration-compliance#vocs-content)

[![Image 1: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

[![Image 2: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Terms of Service
----------------

Per the [terms of service](https://dydx.exchange/v4-terms) of the open-source software, the following categories of persons are currently prohibited from using dYdX Software:

*   Persons or entities who reside in, are located in, are incorporated in, have a registered office in, or are operated or controlled from the United States or Canada;
*   Persons or entities who reside in, are citizens of, are located in, are incorporated in, have a registered office in, or are operated or controlled from Iran, Cuba, North Korea, Syria, Myanmar (Burma), the regions of Crimea, Donetsk or Luhansk, or any other country or region that is the subject of comprehensive country-wide or region-wide economic sanctions by the United States;
*   Persons or entities subject to any economic or trade sanctions administered or enforced by any governmental authority or otherwise designated on any list of prohibited or restricted parties (including the list maintained by the Office of Foreign Assets Control of the U.S. Department of the Treasury);
*   Any other persons or entities whose use of dYdX Software is contrary to any applicable law.

Third parties integrating with the dYdX open-source software are expected to comply with these terms. The client application should block the user from certain countries (see the [list of countries](https://github.com/dydxprotocol/v4-web/blob/633d38dfb837cd80bf2e3e007ecdcaeee2acc658/src/constants/geo.ts#L246) currently blocked).

Geo-Blocking Implementation
---------------------------

### /v4/geo

Third parties are expected to implement geo-blocking themselves but can rely on location information provided by the indexer’s `/v4/geo` endpoint:

```
curl https://api.dydx.exchange/v4/geo
 
{"geo":{"country":"JP","region":"Tokyo","regionCode":"13","city":"Tokyo","timezone":"Asia/Tokyo","ll":[35.6164,139.7425],"metro":null,"blocked":false}
```

The client should call the indexer’s`/v4/compliance/geoblock` endpoint (or `/v4/compliance/geoblock-keplr`, if the user’s connected wallet is Keplr) upon app launching and when the user connects to a new wallet.

This will update the user's compliance status based on the requesting IP. To authenticate the user, sign a message with the user's private key, and send the signed message as part of the payload. See [sample](https://github.com/dydxprotocol/v4-web/blob/main/src/bonsai/rest/compliance.ts#L158) implementation.

### `/v4/screen`

The client can query the compliant status of the user by calling the indexer’s `/v4/screen` endpoint:

```
curl https://indexer.v4testnet.dydx.exchange/v4/compliance/screen/dydx14y0wd820uzr5rd6xu85q5475rg5sk03fsuke3m
 
{"status":"COMPLIANT","reason":null,"updatedAt":"2024-10-24T20:26:15.714Z"}
```

For further information or questions, we can set up a meeting with dYdX’s Legal to discuss specific implementations.
Title: Onboarding

URL Source: https://docs.dydx.xyz/interaction/integration/integration-onboarding

Published Time: Tue, 21 Oct 2025 13:40:12 GMT

Markdown Content:
dYdX address
------------

The client application onboards the user by asking the user to sign a message using an existing wallet address. The v4-client-js library provides a [function](https://github.com/dydxprotocol/v4-clients/blob/a2c7adcc64b33fefaf56ffb6fc1d2bb8b174601e/v4-client-js/src/lib/onboarding.ts#L43) that deterministically generates the dYdX chain address (see [accounts](https://docs.dydx.xyz/concepts/trading/accounts#main-account)) and keys from the signed message. Once the keys are generated, the client application can use them to sign transactions on the dYdX chain on the user’s behalf, enabling secure and seamless interaction with the platform.

The payload doesn't matter to generate a dYdX address, but if you want to deterministically generate a dYdX address that matches what the dYdX Frontend generates, it is best to have the same payload message

```
"message": {
    "action": "dYdX Chain Onboarding"
  }
```

The payload typically looks like this:

Details

```
const ethersWallet = new ethers.Wallet('<wallet>');
const provider = new JsonRpcProvider('https://ethereum.publicnode.com', 1);
const signer = ethersWallet.connect(provider);
 
const signature = await signer.signTypedData(
  {
    name: 'dYdX Chain',
    chainId: 1,
  },
  {
    dYdX: [{ name: 'action', type: 'string' }],
  },
  {
    action: 'dYdX Chain Onboarding',
  },  
);
 
const { mnemonic, privateKey, publicKey } = deriveHDKeyFromEthereumSignature(signature);
```

### Subaccounts

Each main account has 128,001 [subaccounts](https://docs.dydx.xyz/concepts/trading/accounts#subaccounts) Subaccounts 0 to 127 are parent subaccounts. Parent subaccounts can have multiple positions opened and all positions are cross-margined. Subaccounts 128 to 128,000 are child subaccounts and are isolated margin. Child subaccounts will only ever have up to 1 position open.

Deposits and Withdrawals
------------------------

### Deposits

Deposits are in three steps.

### Deposit Tx

First, the client calls Skip’s API to construct the transaction that routes the fund from the source chain to Noble. Users would need to sign and send this transaction from their wallet.

### Noble poll

The client then polls the balance at the user's Noble address, and when the fund arrives, it would sign (using the user’s dYdX key pair) and send it over to the dYdX chain (see [here](https://github.com/dydxprotocol/v4-web/blob/71bd9c7f85512fe1893fd656968011cf75b106e6/src/bonsai/lifecycles/nobleBalanceSweepLifecycle.ts#L119)).

### Transfer Subaccount

Lastly, after the fund arrives at dYdX, the client moves the fund from the user's main account to the [subaccount](https://docs.dydx.xyz/node-client/private#transfer) for trading.

### Withdrawals

The withdrawal is the reverse process of deposit.

### Transfer Main Account

First, the fund needs to be moved from the user's subaccount to the main account.

### Withdrawal Tx

Then, a withdrawal transaction is constructed to send the fund to the destination chain/address. The withdrawal transaction contains two child transactions:

1.   sending from dYdX chain to Noble chain,
2.   Noble to destination chain (obtained from the Skip route API). See [here](https://github.com/dydxprotocol/v4-web/blob/71bd9c7f85512fe1893fd656968011cf75b106e6/src/hooks/useSubaccount.tsx#L156).

Skip Go API
-----------

Users must deposit Noble USDC as collateral into the dYdX chain to begin trading. The dYdX chain uses USDC. To construct the route for deposits and withdrawals, we recommend using Skip Go, either through the [Typescript client](https://docs.skip.build/go/client/getting-started) or by calling the [APIs](https://docs.skip.build/go/general/getting-started) directly. There are endpoints to get the supported [chains](https://docs.skip.build/go/api-reference/prod/info/get-v2infochains) and [tokens](https://docs.skip.build/go/api-reference/prod/fungible/get-v2fungibleassets). To initiate a deposit or withdrawal,

### Call endpoint

first call the [route](https://docs.skip.build/go/api-reference/prod/fungible/post-v2fungibleroute) endpoint to fetch the route.

Sample route fetch request for deposit looks like this:

```
curl 'https://api.skip.build/v2/fungible/route' \
  -H 'accept: application/json, text/plain, */*' \
  -H 'content-type: application/json' \
  --data-raw '{"source_asset_denom":"0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48","source_asset_chain_id":"1","dest_asset_denom":"ibc/8E27BA2D5493AF5636760E354E46004562C46AB7EC0CC4C1CA14E9E20E2545B5","dest_asset_chain_id":"dydx-mainnet-1","cumulative_affiliate_fee_bps":"0","allow_unsafe":true,"smart_relay":true,"smart_swap_options":{"split_routes":false,"evm_swaps":true},"amount_in":"10000000"}'
```

Here `ibc/8E27BA2D5493AF5636760E354E46004562C46AB7EC0CC4C1CA14E9E20E2545B5` is the USDC denom of the dYdX Chain.

### Set Bridge option

Set the [bridges](https://docs.skip.build/go/api-reference/prod/fungible/post-v2fungibleroute#body-bridges) option to include `“CCTP”`, `“GO_FAST”`, `“IBC”`, and `“AXELAR”`.

You can also set the [go_fast](https://docs.skip.build/go/api-reference/prod/fungible/post-v2fungibleroute#body-go-fast) to `true` for selected chains/and tokens (see [here](https://docs.skip.build/go/advanced-transfer/go-fast)), which would return a route that can be completed within 10 seconds.

The route endpoint will return the estimated time and fees for the transfer that can be shown to the user.

### Msgs endpoint

After user accepts the route, call the [msgs](https://docs.skip.build/go/api-reference/prod/fungible/post-v2fungiblemsgs) endpoint and passing the operations returned from the `route` response payload to fetch the transaction data:

```
curl 'https://api.skip.build/v2/fungible/msgs' \
  -H 'accept: application/json, text/plain, */*' \
  -H 'content-type: application/json' \
  --data-raw '{"source_asset_denom":"0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48","source_asset_chain_id":"1","dest_asset_denom":"ibc/8E27BA2D5493AF5636760E354E46004562C46AB7EC0CC4C1CA14E9E20E2545B5","dest_asset_chain_id":"dydx-mainnet-1","amount_in":"10000000","amount_out":"9980000","address_list":["0x0765CA6d3DC4fa6d6638781BA8414A1f5eFbfAd8","dydx1k93udthd0vtzjk465f846qzea3fzq7axnmfqyz"],"operations":[{"tx_index":0,"amount_in":"10000000","amount_out":"9980000","cctp_transfer":{"from_chain_id":"1","to_chain_id":"noble-1","burn_token":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48","bridge_id":"CCTP","denom_in":"0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48","denom_out":"uusdc","smart_relay":true,"smart_relay_fee_quote":{"fee_amount":"20000","relayer_address":"noble1dyw0geqa2cy0ppdjcxfpzusjpwmq85r5a35hqe","expiration":"2025-03-14T00:52:56Z","fee_payment_address":"0xBC8552339dA68EB65C8b88B414B5854E0E366cFc","fee_denom":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"}}},{"tx_index":0,"amount_in":"9980000","amount_out":"9980000","transfer":{"port":"transfer","channel":"channel-33","from_chain_id":"noble-1","to_chain_id":"dydx-mainnet-1","pfm_enabled":true,"supports_memo":true,"denom_in":"uusdc","denom_out":"ibc/8E27BA2D5493AF5636760E354E46004562C46AB7EC0CC4C1CA14E9E20E2545B5","bridge_id":"IBC","dest_denom":"ibc/8E27BA2D5493AF5636760E354E46004562C46AB7EC0CC4C1CA14E9E20E2545B5","chain_id":"noble-1","smart_relay":false}}],"estimated_amount_out":"9980000","slippage_tolerance_percent":"1"}'
```

Here, `dydx1k93udthd0vtzjk465f846qzea3fzq7axnmfqyz` is the user's dYdX chain address obtained from the Onboarding step.

To obtain the relay address for Noble, Osmosis and Neutron, do conversion from the dYdX address as follows

```
dydx_address="dydx1kgjgvl3xer7rwskp6tlynmjrd2juas6nqxn8yg"  
     noble_address=bech32.bech32_encode("noble", bech32.bech32_decode(dydx_address)[1])
     osmosis_address=bech32.bech32_encode("osmo", bech32.bech32_decode(dydx_address)[1]
     neutron_address=bech32.bech32_encode("neutron", bech32.bech32_decode(dydx_address)[1])
```

### Submit TX

The `route` and `msgs` calls can be combined into one call to [msgs_direct](https://docs.skip.build/go/api-reference/prod/fungible/post-v2fungiblemsgs_direct).

To submit the transaction, the transaction payload data from the `msgs` or `msgs_direct` should be submitted via the user wallet.

### Go Fast Supported Tokens & Chains

*   Go Fast supports `any EVM` asset on the supported source chains that can be swapped to USDC.
*   Any asset on the `Cosmos side` that can be swapped from USDC is also supported.
*   This includes `instant deposit` support for assets like ETH on Ethereum, which can be instantly converted to USDC on dYdX.
*   If a chain has `instant finality` and `IBC compatibility`, transfers can be near-instant, making it functionally similar to Instant Deposit.
*   `Chains not supported by CCTP` will not have Instant Deposit functionality but can still use IBC for transfers.
*   For an exhaustive list of supported tokens, reference the [Skip Go documentation](https://docs.skip.build/go/advanced-transfer/go-fast).
Title: Market data

URL Source: https://docs.dydx.xyz/interaction/integration/integration-markets

Published Time: Tue, 14 Oct 2025 13:33:08 GMT

Markdown Content:
The client application typically displays a list of tradable and launchable markets as follows:

![Image 1: markets1](https://docs.dydx.xyz/markets1.png)

![Image 2: markets2](https://docs.dydx.xyz/markets2.png)

The market list can be obtained from the Indexer in two ways:

1.   REST API: Call `GET`[/perpetualMarkets](https://docs.dydx.xyz/indexer-client/http#get-perpetual-markets).
2.   WebSocket Subscription: Subscribe to the [v4-markets](https://docs.dydx.xyz/indexer-client/websockets#markets) channel (preferred, as it provides real-time updates).

Additionally, the client should call `metadata-service/v1/info` to retrieve static market data, such as market icons and other metadata.

### Market Data Display Fields

(a)`Market Icon`: Extracted from the logo field in the `metadata-service/v1/info` response.

(b) `Market Name`: Derived from the name field in `metadata-service/v1/info` or directly from the market token name in the Indexer data.

(c) `Oracle Price`: Provided by the Indexer.

(d) `Perp 24h Price Change (%)`: Available in the Indexer’s `priceChange24H` field.

(e) `Perp Trade Volume`: Extracted from the Indexer’s `volume24H` field.

(f) `Spot Market Cap`: Found in the `market_cap` field of the `metadata-service/v1/prices` response.

(g) `User’s Buying Power`: Determined by applying collateral to the market (explained in the user-specific data section).

(h) `Perp Open Interest`: Retrieved from the Indexer’s `openInterest` field.

(i)`Perp Funding Rate`: Available in the Indexer’s `nextFundingRate` field.

(j) `Market Descriptions`: Sourced from the `v4-localization` repository, using the token ID as the key.

(k) `Market Info Links`: Obtained from the url field in `metadata-service/v1/info`.

Candles
-------

The candles data come from the websocket `v4-candles` channel. To subscribe the channel, supply the following parameters:

```
{
“id”: “ETH-USD/1HOUR”
“batch”: “true
}
```

Supply the id field with the market ID and the [candle resolution](https://docs.dydx.xyz/types/candle_resolution). Parse [CandleResponse](https://docs.dydx.xyz/types/candle_response_object) to get the list of the candle values.

![Image 3: candles](https://docs.dydx.xyz/candles.png)

(a) `Candlestick`. Use the `high`, `low`, `open` and `close` field from each data point. See [here](https://www.investopedia.com/trading/candlestick-charting-what-is-it/) for candles.

(b) `Volume`. Use the `usdVolume` field.

(c) `Candle resolution`[candle resolution](https://docs.dydx.xyz/types/candle_resolution).

Orderbook
---------

The orderbook data come from the websocket [v4_orderbook](https://docs.dydx.xyz/indexer-client/websockets#orders) channel, which gives a list of asks and bids:

```
"bids": [    
  {       
 "price": "28194",       
 "size": "4.764826096"     
  },
  ...
],
"asks": [    
  {       
 "price": "28294",       
 "size": "5.764826096"     
  },
  ...
],
```

### Order Book Displaying Fields

![Image 4: orderbook](https://docs.dydx.xyz/orderbook.png)

(a) `Size of the order`

(b) `Price of the order`

### Order Book Color

*   `Darker green bar`: Represents the size of an `individual order`.
*   `Light green bar`: Represents the `depth at this price`, calculated as the `sum of all order sizes` that would have been taken before this order is crossed. See [here](https://academy.youngplatform.com/en/trading/order-book/) for depth.

### Handling WebSocket Updates

When the `WebSocket channel` sends an update, the client `must update the order book` in memory using the order price as the key.

#### Add/Update/Delete Entries

*   `Add or update` an entry if the backend sends an order with a non-zero size.
*   `Remove` an entry if the backend sends an order with `zero size` (indicating the order was canceled or taken).

#### Remove Crossed Entries

*   After updating the order book, the client should `remove any crossed entries` when the lowest ask price > highest bid price.
*   This ensures that only valid bid-ask pairs remain in the order book.
Title: User Portfolio

URL Source: https://docs.dydx.xyz/interaction/integration/integration-portfolio

Published Time: Tue, 21 Oct 2025 21:42:31 GMT

Markdown Content:
After onboarding to dYdX and depositing funds, the app displays the portfolio view. Once the user places a trade, the app updates to show open positions.

Portfolio Data Display Fields
-----------------------------

![Image 1: portfolio1](https://docs.dydx.xyz/portfolio1.png)

![Image 2: portfolio2](https://docs.dydx.xyz/portfolio2.png)

(a) `Account equity`: Indexer data from the websocket `v4_parent_subaccounts` channel. [response](https://docs.dydx.xyz/types/parent_subaccounts_update_message). This is equity of subaccount 0 (e.g., the sum of all child subaccount equities).

(b) `Account PnL`: `Account PNL` of the selected time range (e.g., it’s “7 days” on the screenshot). Indexer data [GetHistoricalPnlForParentSubaccount](https://docs.dydx.xyz/indexer-client/http#get-parent-historical-pnl). Sample curl request:

`curl --location 'https://indexer.v4testnet.dydx.exchange/v4/historical-pnl/parentSubaccountNumber?address=dydx1k93udthd0vtzjk465f846qzea3fzq7axnmfqyz&parentSubaccountNumber=0'`

(c) `max buying power`: The endpoint returns the PNL ticks of the given time range. The value is the difference between the last and first tick.

Account level buying power. The Indexer provides data via the WebSocket `v4_parent_subaccounts` channel. [response](https://docs.dydx.xyz/types/parent_subaccounts_update_message).

#### Calculate max leverage

Each market has a configured maximum leverage factor ranging from 1x to 50x. The leverage factor is derived from the `initialMarginFraction` field in the market info received from the WebSocket [v4-markets](https://docs.dydx.xyz/indexer-client/websockets#markets) channel.

`max leverage = 1 / initialMarginFraction`

#### Max Buying power

The `max buying power` is then calculated as follows:

*   Take the `freeCollateral` of `subaccount 0`
*   Multiply it by the `maximum leverage` across all markets (50x)

This represents the user's maximum buying power if all remaining free collateral is applied to the market with the highest leverage.

(d) `Account level risk` The account-level risk is derived from Indexer data via the WebSocket `v4_parent_subaccounts` channel. [sample response](https://docs.dydx.xyz/types/parent_subaccounts_update_message).

This metric represents the `percentage of the user's total collateral` that has been allocated to support open positions (also referred to as `margin`). The account-level risk is derived from Indexer data via the WebSocket `v4_parent_subaccounts` channel. [sample response](https://docs.dydx.xyz/types/parent_subaccounts_update_message).

To compute `total collateral`, follow these steps:

#### Collateral per position

Calculate the collateral for each open position:

`position collateral = (current value of the position) * leverage = (position size * current oracle price) * leverage`

#### Sum collateral

Sum up the collaterals for all open positions.

#### Total collateral

Add the USDC asset position of subaccount 0, which represents the remaining USDC balance that hasn’t been used as collateral for open positions.

The resulting `total collateral` is then used to determine the `margin percentage`, reflecting the level of risk associated with the account’s open positions.

(e) `Historical PNL`. Indexer data [GetHistoricalPnlForParentSubaccount](https://docs.dydx.xyz/indexer-client/http#get-parent-historical-pnl). The chart shows the PNL tickets of the selected time range.

(f) `Position size, and position side` Indexer data from the websocket `v4_parent_subaccounts` channel. [sample response](https://docs.dydx.xyz/types/parent_subaccounts_update_message). Subaccount -> ChildSubaccounts -> openPerpetualPositions -> size/side.

(g) `Current oracle price`. From market data off the Websocket [v4-markets](https://docs.dydx.xyz/indexer-client/websockets#markets) channel.

(i (img 1)) `Perp 24h price change percentage`: From market data off the Websocket [v4-markets](https://docs.dydx.xyz/indexer-client/websockets#markets) channel, priceChange24H field of childSubaccount.

(i (img 2)) `Position USDC size`. Position size * oracle price

(j) `Position PNL`. (Position size * oracle price) - (Position size * entry_price)

(k) `Current funding rate`. netFunding, of childSubaccount.

(l) `Entry price`. entryPrice, of childSubaccount

(m) `Liquidation price`. When the market price moves across this estimated price, the user's position would be liquidated. See [margining requirements](https://docs.dydx.xyz/concepts/trading/margin)

History
-------

The trade history data come from the Indexer’s [getfillsforparentsubaccount](https://docs.dydx.xyz/indexer-client/http#get-parent-fills) endpoint. Transfer history data come from the Indexer’s [gettransfersforparentsubaccount](https://docs.dydx.xyz/indexer-client/http#get-parent-transfers) endpoint.

![Image 3: history](https://docs.dydx.xyz/history.png)
Title: Placing a Trade

URL Source: https://docs.dydx.xyz/interaction/integration/integration-trade

Markdown Content:
Market Order (Simple Trade)
---------------------------

Market trade lets users execute an order based on the current state of the orderbook.

![Image 1: marketorder](https://docs.dydx.xyz/marketorder.png)

(a) `Trade size in USD`.

(b) `Trade size in native token`. This value should be dynamically updated based on the trade size in USD and the current state of the order book. Order Fulfillment Process (See [link](https://github.com/dydxprotocol/v4-abacus/blob/f3802563c06422eb5a3de0b1e48719fb279fab71/src/commonMain/kotlin/exchange.dydx.abacus/calculator/V2/TradeInput/TradeInputMarketOrderCalculator.kt#L379) for an implementation):

1.   Iterate through the order book from the top (best price first).
2.   Attempt to fill the order by consuming liquidity until the requested USDC size is met.
3.   Sum up the native token size from the orders used in the process.

The toggle button to the right would toggle the input between (a) and (b).

(c) `Maximum amount` that can be entered into (a). The maximum order amount is constrained by:

1.   The maximum leverage of the selected token market.
2.   The user’s remaining free collateral.

This is similar to previous calculations, but with an additional consideration for current pending orders.

### Adjustments for Existing Positions

*   If the proposed order modifies an existing position in the same token market, the displayed buying power must be adjusted accordingly:
*   If the new order is in the same direction (LONG on top of LONG, SHORT on top of SHORT): The buying power remains unchanged.
*   If the new order is in the opposite direction (LONG on top of SHORT, SHORT on top of LONG): The buying power increases since closing the existing position frees up collateral.

Example Calculation:

*   Current buying power: $500
*   Existing position: LONG ETH-USD, worth $100

| New Order Type | Adjusted Buying Power |
| --- | --- |
| LONG ETH-USD | $500 (unchanged) |
| SHORT ETH-USD | $700 (increased by $200) |

This adjustment ensures that users see the correct available buying power based on their current open positions and pending orders.

(d) `Account level risk`. Same as here, except taking into account the current pending order.

(e) `Fees`. Each user belongs to a fee tier depending on the volume of trades that have executed. The actual fee is the USD size of the trade multiplied by the fee rate associated with the fee tier. To get the [current fee tier](https://docs.dydx.xyz/node-client/public/get_user_fee_tier) of the user, call validator’s RPC UserFeeTier endpoint (see [example](https://github.com/dydxprotocol/v4-clients/blob/9e77056451944c15c4625854da96de5e023e429d/v4-client-js/src/clients/modules/get.ts#L99)).

### Market Order Submission

To submit a market order, the client can use the [placeOrder](https://docs.dydx.xyz/node-client/private#place-order) function of the v4-client-js library with the following parameters:

*   type=”MARKET”
*   timeInForce = “IOC”
*   price = value from (a) / value from (b) * (1+slippage_threhold), where slippage_threhold = 0.05
*   clientId = [some unique random id]

The validator will return an error if the input is invalid, meaning client-side validation is not strictly necessary. However, it is recommended that the client application validates user input before submitting an order to enhance the user experience by preventing unnecessary errors and reducing failed transactions [sample validation logic](https://github.com/dydxprotocol/v4-abacus/blob/f3802563c06422eb5a3de0b1e48719fb279fab71/src/commonMain/kotlin/exchange.dydx.abacus/validator/TradeInputValidator.kt#L26).

Pending orders will be returned from the websocket `v4_parent_subaccounts` channel [sample response]. Each [order](https://docs.dydx.xyz/types/order) in the list will contain a `clientId` field, which the client can match against the trade submission payload’s clientId.

Once the order is executed, the `openPerpetualPositions` field from the websocket `v4_parent_subaccount` channel will have the position added or updated.

### Closing a Position

To close an existing position, submit a market order using the [placeOrder](https://docs.dydx.xyz/node-client/private#place-order) function of the `v4-client-js` library with the position size as the “size” field. Make the “side” to be the opposite of the position side, and reduceOnly to “true”.

Once the order is executed, the openPerpetualPositions field from the websocket `v4_parent_subaccount` channel will have the existing position removed.

### Pro Trade (Limit, Take Profit, Stop Loss, etc)

[TO-DO]

Trigger Orders
--------------

Users can add take profit and stop loss triggers to existing positions.

![Image 2: triggerorder](https://docs.dydx.xyz/triggerorder.png)

To find existing trigger orders associated with the current position, examine the `“orders”` list returned from the websocket `v4_parent_subaccounts` channel. A sample response:

```
"orders": [
     {
       "id": "ff6d83c1-a2e7-5fa9-9362-3fbc4771aec3",
       "subaccountId": "4adcda50-be50-596e-b3b0-d70cd3ca193d",
       "clientId": "1741547162",
       "clobPairId": "0",
       "side": "SELL",
       "size": "0.001",
       "totalFilled": "0",
       "price": "97510",
       "type": "TAKE_PROFIT",
       "status": "UNTRIGGERED",
       "timeInForce": "IOC",
       "reduceOnly": true,
       "orderFlags": "32",
       "goodTilBlockTime": "2025-06-09T17:00:16.000Z",
       "createdAtHeight": "34142063",
       "clientMetadata": "1",
       "triggerPrice": "102643",
       "updatedAt": "2025-03-11T17:00:16.521Z",
       "updatedAtHeight": "34142063",
       "postOnly": false,
       "ticker": "BTC-USD",
       "subaccountNumber": 0
     }
   ],
```

*   `ticker` field: Must match the `market ID` of the`open position`.
*   `side` field: Should be the `opposite` of the `open position` side:
    *   If the open position is `LONG`, the order side should be `SELL`.
    *   If the open position is `SHORT`, the order side should be `BUY`.

*   status field: Must be set to `UNTRIGGERED`.
*   type field: Can be either `TAKE_PROFIT` or `STOP_MARKET`.

Existing trigger order associated with the current position should be displayed as follows:

(a) The price field of the `TAKE_PROFIT` order

(b) The gain percent is calculated from the `entry_price` field of the open position and (a). For example, if `entry_price` is $100, and (a) is $110, the gain percentage is 10%.

(c) Same as (a) except for a `STOP_MARKET` order

(d) Same as (b) except for a `STOP_MARKET` order

The client can modify a trigger order state by performing two operations:

1.   `Add` a new trigger order
2.   `Cancel` an existing order

### Updating the Price of an Existing Trigger Order

If the user updates the price of an existing trigger order, the client must first cancel the existing order before adding the new one. This ensures that only the latest order remains active and prevents conflicting trigger conditions. To submit a trigger order, the client can use the [placeOrder](https://docs.dydx.xyz/node-client/private#place-order) function of the v4-client-js library with the following parameters:

*   type=”TAKE_PROFIT_MARKET”, or “STOP_MARKET”
*   triggerPrice = Trigger price entered by the user
*   price = triggerPrice * (1+slippage_threhold), where slippage_threhold = [0.05, 0.1]
*   execution = “IOC”
*   timeInForce = null
*   reduceOnly = “true”
*   clientId = [some unique random id]

To cancel an existing trigger order, the client can call the [cancelOrder](https://docs.dydx.xyz/node-client/private#cancel-order) function of the `v4-client-js` library.
Title: Builder Codes

URL Source: https://docs.dydx.xyz/interaction/integration/integration-builder-codes

Published Time: Tue, 21 Oct 2025 21:43:05 GMT

Markdown Content:
Builder codes enables external parties to submit orders to dYdX and collect fees (per-order) for building and routing an order to the exchange. The address and fee, in parts per million, needs to be configured via the `BuilderCodeParameters` in the order message itself. The fee will be paid out when the given order is filled.

Builder fees and addresses can be queried via the indexer using the `/orders` and `/fills` endpoints as usual. `/orders` contains details on the fee rate and builder address. `/fills` also contains the builder address as well as details on the amount charged per-fill.

Changes To The Order Message
----------------------------

BuilderCodeParameters
---------------------

`BuilderCodeParameters` is an addition to the order message which will specify:

*   `partner address` - where fees will be routed
*   `fee (in ppm)` that will be charged on order matching

```
message Order {
  // The unique ID of this order. Meant to be unique across all orders.
  OrderId order_id = 1 [ (gogoproto.nullable) = false ];
	
	...
	
	// builder_code is the metadata for the partner or builder of an order.
  BuilderCodeParameters builder_code_params = 12;
}
 
// BuilderCodeParameters represents the metadata for the 
// partner or builder of an order. This allows them to 
// specify a fee for providing there service
// which will be paid out in the event of an order fill.
message BuilderCodeParameters {
  // The address of the builder to which the fee will be paid.
  string builder_address = 1;
 
  // The fee enforced on the order in ppm.
  uint32 fee_ppm = 2;
}
```

Order Validation Checks
-----------------------

*   Ensure the `builder address` is valid
*   Ensure the `feePPM` is in the range `(0, 10,000]`
Title: Revenue Share

URL Source: https://docs.dydx.xyz/interaction/integration/integration-revshare

Markdown Content:
Order Router Rev Share enables third-party order routers to direct orders to dYdX and earn a portion of the trading fees (maker and taker). The revenue share, specified in parts per million (ppm), must be voted in via Governance and set in the `order_router_address` field in the order message itself.

The revenue will be distributed based on filled orders that were routed through the participating order router.

Order router details and revenue share percentages can be monitored through the indexer using the `/orders` and `/fills` endpoints. The `/orders` endpoint provides information on the order router address, while the `/fills` endpoint shows the order router address and the specific revenue amount distributed per fill.

To participate in the Order Router Rev Share program, users need to propose and have a passing vote for their order router address & revenue split.

*   Affiliate revenue takes priority in the distribution hierarchy.
*   If there is an active affiliate split that has not reached its maximum within a 30-day rolling window, no revenue will be shared with the order router

Implementation Details
----------------------

Voting in via Governance
------------------------

To participate in the Order Router Rev Share program, you need to create and submit a governance proposal. Below is an example of what the governance message structure looks like:

```
message Order {
"messages": [
	{
		"@type": "/dydxprotocol.revshare.MsgSetOrderRouterRevShare",
		"authority": authority,
		"order_router_rev_share": {
			"address": {{your address}},
			"share_ppm": {{your requested ppm}},
		}
	}
]
}
```

The key components of this message are:

*   `address` - The address of the order router that will receive the revenue share. This is also the id you place in your order message
*   `sharePpm` - The revenue share percentage in parts per million (ppm).

After submitting the proposal, it must go through the standard governance voting process and receive a passing vote before the order router address and revenue share percentage are activated in the system.

Updating Revenue Share (Optional)
---------------------------------

The process for updating an existing order router's revenue share is the same as setting up a new one. You will need to submit a governance proposal with the updated parameters.

To update the revenue share percentage for an existing order router, create a governance message with the same structure:

```
"messages": [
	{
		"@type": "/dydxprotocol.revshare.MsgSetOrderRouterRevShare",
		"authority": authority,
		"order_router_rev_share": {
			"address": {{your existing address}},
			"share_ppm": {{your new requested ppm}},
		}
	}
]
```

The proposal must go through the standard governance voting process and receive a passing vote before the updated revenue share percentage takes effect.

Deleting an Order Router Rev Share (Optional)
---------------------------------------------

To delete an order router's revenue share configuration, you simply need to set the revenue share percentage to 0. This process follows the same governance workflow as setting up or updating a revenue share.

Submit a governance proposal with the following message structure:

```
"messages": [
	{
		"@type": "/dydxprotocol.revshare.MsgSetOrderRouterRevShare",
		"authority": authority,
		"order_router_rev_share": {
			"address": {{your existing address}},
			"share_ppm": 0,
		}
	}
]
```

Changes to the Order Message
----------------------------

The `order_router_address` field is set when an order is placed

*   `order_router_address` - the ID of the order router and where fees will be sent to

```
message Order {
  // The unique ID of this order. Meant to be unique across all orders.
  OrderId order_id = 1 [ (gogoproto.nullable) = false ];
  ...
  // order_router_address is the metadata for the frontend order router.
  string order_router_address = 13;
}
```

Order Validation Checks
-----------------------

*   Ensure the `order_router_address` field is valid and already voted in via governance
