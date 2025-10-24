Title: Intro to dYdX Chain Architecture

URL Source: https://docs.dydx.xyz/concepts/architecture/overview

Published Time: Tue, 21 Oct 2025 18:35:55 GMT

Markdown Content:
### System Architecture

dYdX Chain (sometimes referred to as "v4") has been designed to be completely decentralized end-to-end. The main components broadly include the protocol, the Indexer, and the front end. Each of these components are available as open source software. None of the components are run by dYdX Trading Inc.

![Image 1: image](https://docs.dydx.xyz/system-architecture.png)

### Protocol (or "Application")

The open-source protocol is an L1 blockchain built on top of [CometBFT](https://dydx.exchange/blog/v4-technical-architecture-overview#:~:text=on%20top%20of-,CometBFT,-and%20using%20CosmosSDK) and using [CosmosSDK](https://docs.cosmos.network/). The node software is written in Go, and compiles to a single binary. Like all CosmosSDK blockchains, dYdX Chain uses a proof-of-stake consensus mechanism.

The protocol is supported by a network of nodes. There are two types of nodes:

*   **Validators**: Validators are responsible for storing orders in an in-memory orderbook (i.e. off chain and not committed to consensus), gossipping transactions to other validators, and producing new blocks for dYdX Chain through the consensus process. The consensus process will have validators take turns as the proposer of new blocks in a weighted-round-robin fashion (weighted by the number of tokens staked to their node). The proposer is responsible for proposing the contents of the next block. When an order gets matched, the proposer adds it to their proposed block and initiates a consensus round. If ⅔ or more of the validators (by stake weight) approve of a block, then the block is considered committed and added to the blockchain. Users will submit transactions directly to validators.

*   **Full Nodes**: A Full Node represents a process running the dYdX Chain open-source application that does not participate in consensus. It is a node with 0 stake weight and it does not submit proposals or vote on them. However, full nodes are connected to the network of validators, participate in the gossiping of transactions, and also process each new committed block. Full nodes have a complete view of a dYdX Chain and its history, and are intended to support the Indexer. Some parties may decide (either for performance or cost reasons) to run their own full node and/or Indexer.

### Indexer

The Indexer is a read-only collection of services whose purpose is to index and serve blockchain data to end users in a more efficient and web2-friendly way. This is done by consuming real time data from a dYdX Chain full node, storing it in a database, and serving that data through a WebSocket and REST requests to end-users.

While the dYdX Chain open-source protocol itself is capable of exposing endpoints to service queries about some basic onchain data, those queries tend to be slow as validators and full nodes are not optimized to efficiently handle them. Additionally, an excess of queries to a validator can impair its ability to participate in consensus. For this reason, many Cosmos validators tend to disable these APIs in production. This is why it is important to build and maintain Indexer and full-node software separate from validator software.

Indexers use Postgres databases to store onchain data, Redis for offchain data, and Kafka for consuming and streaming on/offchain data to the various Indexer services.

### Front-ends

In service of building an end-to-end decentralized experience, dYdX has built three open-source front ends: a web app, an iOS app, and an Android app.

*   **Web application**: The website was built using JavaScript and React. The website interacts with the Indexer through an API to get offchain orderbook information and will send trades directly to the chain. dYdX has open sourced the front-end codebase and associated deployment scripts. This allows anyone to easily deploy and access the dYdX front end to/from their own domain/hosting solution via IPFS/Cloudflare gateway.

*   **Mobile**: The iOS and Android apps are built in native Swift and Kotlin, respectively. The mobile apps interact with the Indexer in the same way the web application does, and will send trades directly to the chain. The mobile apps have been open sourced as well, allowing anyone to deploy the mobile app to the App Store or Play store. Specifically for the App store, the deployer needs to have a developer account as well as a Bitrise account to go through the app submission process.

### Order Entry Gateway Service (OEGS) ?

The Order Entry Gateway represents the next step in dYdX’s multi-stage performance evolution and is made possible by the following 2 designs:

1.   Designated proposers — A governance-selected subset of validators responsible for proposing blocks. This creates a predictable topology for faster routing (available in v9 software upgrade).
2.   Order Entry Gateway Service (OEGS) — open-sourced infrastructure that provides a direct, optimized path from traders to the proposer set, reducing latency, increasing throughput, and lowering barriers for professional and retail traders alike (available now on testnet).

### Lifecycle of an Order

Now that we have a better understanding of each of the components of dYdX Chain, let's take a look at how it all comes together when placing an order. When an order is placed on dYdX Chain, it follows the flow below:

1.   User places a trade on a decentralized front end (e.g., website) or via API
2.   The order is routed to a validator. That validator gossips that transaction to other validators and full nodes to update their orderbooks with the new order.
3.   The consensus process picks one validator to be the proposer. The selected validator matches the order and adds it to its next proposed block.
4.   The proposed block continues through the consensus process.
    1.   If ⅔ of validator nodes vote to confirm the block, then the block is committed and saved to the onchain databases of all validators and full nodes.
    2.   If the proposed block does not successfully hit the ⅔ threshold, then the block is rejected.

5.   After the block is committed, the updated onchain (and offchain) data is streamed from full nodes to Indexers. The Indexer then makes this data available via API and WebSockets back to the front end and/or any other outside services querying for this data.
Title: Indexer Deep Dive

URL Source: https://docs.dydx.xyz/concepts/architecture/indexer

Markdown Content:
A good way to think about the Indexer is as similar to Infura or Alchemy’s role in the Ethereum ecosystem. However, unlike Infura/Alchemy, and like everything else in dYdX Chain, the Indexer is completely open source and can be run by anyone!

### What is the Indexer?

As part of tooling for the dYdX ecosystem, we want to ensure that clients have access to performant data queries when using exchanges running on dYdX Chain software. Cosmos SDK Full Nodes offer a number of APIs that can be used to request onchain data. However, these Full Nodes are optimized for committing and executing blocks, not for serving high frequency, low-latency requests from web/mobile clients.

This is why we wrote software for an indexing service. The Indexer is a read-only service that serves off chain data to clients over REST APIs and Websockets. Its purpose is to store and serve data that exists on dYdX Chain in an easier to use way. In other words, the purpose of an indexer is to index and serve data to clients in a more performant, efficient and web2-friendly way. For example the indexer will serve websockets that provide updates on the state of the orderbook and fills. These clients will include front-end applications (mobile and web), market makers, institutions, and any other parties looking to query dYdX Chain data via a traditional web2 API.

### Onchain vs. Offchain data

The Indexer will run two separate ingestion/storage processes with data from a v4 Full Node: one for onchain data and one for offchain data. Currently, throughput of onchain data state changes is expected to be from 10-50 events/second. On the other hand, the expected throughput of offchain data state changes is between 500-1,000 events/second. This represents a 10-100x difference in throughput requirements. By handling these data types separately, v4 is built to allow for different services to better scale according to throughput requirements.

### Onchain Data

Onchain data is all data that can be reproduced by reading committed transactions on a dYdX Chain deployment. All onchain data has been validated through consensus. This data includes:

1.   Account balances (USDC)
2.   Account positions (open interest)
3.   Order Fills
    1.   Trades
    2.   Liquidations
    3.   Deleveraging
    4.   Partially and completely filled orders

4.   Funding rate payments
5.   Trade fees
6.   Historical oracle prices (spot prices used to compute funding and process liquidations)
7.   Long-term order placement and cancellation
8.   Conditional order placement and cancellation

### Offchain Data

Offchain data is data that is kept in-memory on each v4 node. It is not written to the blockchain or stored in the application state. This data cannot be queried via the gRPC API on v4 nodes, nor can it be derived from data stored in blocks. It is effectively ephemeral data on the v4 node that gets lost on restarts/purging of data from in-memory data stores. This includes:

1.   Short-term order placement and cancellations
2.   Order book of each perpetual exchange pair
3.   Indexed order updates before they hit the chain

Indexer Architecture
--------------------

![Image 1: image](https://docs.dydx.xyz/indexer-architecture.png)

The Indexer is made up of a series of services that ingest information from v4 Full Nodes and serve that information to various clients. Kafka topics are used to pass events/data around to the services within the Indexer. The key services that make up Indexer are outlined below.

### Ender (Onchain ingestion)

Ender is the Indexer’s onchain data ingestion service. It consumes data from the “to-ender” Kafka topic (which queues all onchain events by block) and each payload will include all event data for an entire block. Ender takes all state changes from that block and applies them to a Postgres database for the Indexer storing all onchain data. Ender will also create and send websocket events via a “to-websocket-?” Kafka topic for any websocket events that need to be emitted.

### Vulcan (Offchain ingestion)

Vulcan is the Indexer’s offchain data ingestion service. It will consume data from the “to-vulcan” Kafka topic (queues all offchain events), which will carry payloads that include active order book updates, place order updates, cancel order updates, and optimistic fills. This data will be stored in a Redis cache. Vulcan will update Redis with any new open orders, set the status of canceled orders to cancel pending, and update orderbooks based on the payload received. Vulcan will also update Postgres whenever a partially filled order is canceled to update the state of the order in Postgres. Vulcan will also create and send websocket events via a “to-websocket-?” Kafka topic for any websocket events that need to be emitted.

### Comlink (API Server)

Comlink is an API server that will expose REST API endpoints to read both onchain and offchain data. For example, a user could request their USDC balance or the size of a particular position through Comlink, and would receive a formatted JSON response.

As an explicit goal set out by the dYdX team, we’re designing v4 APIs to closely match the [v3 APIs](https://dydx.exchange/blog/v4-deep-dive-indexer#:~:text=closely%20match%20the-,v3%20exchange%20APIs,-.%20We%20have%20had). We have had time to gather feedback and iterate on these APIs over time with v3, and have confidence that they are reasonable at the product-level.

### Roundtable

Roundtable is a periodic job service that provides required exchange aggregation computations. Examples of these computations include: 24h volume per market, open interest, PnL by account, candles, etc.

### Socks (Websocket service)

Socks is the Indexer’s websockets service that allows for real-time communication between clients and the Indexer. It will consume data from ender, vulcan, and roundtable, and send websocket messages to connected clients.

Hosting & Deploying the Indexer
-------------------------------

In service of creating an end-to-end decentralized product, the Indexer will be open source. This will include comprehensive documentation about all services and systems, as well as infrastructure-as-code for running the Indexer on popular cloud providers.

The specific responsibilities of a third party operator looking to host the Indexer generally include initial deployment and ongoing maintenance.

Initial deployment will involve:

*   Setting up AWS infrastructure to utilize the open-source repo.
*   Deploying Indexer code to ingest data from a full-node and expost that information through APIs and websockets
*   Datadog (provides useful metrics and monitoring for Indexer services), and Bugsnag (real-time alerting on bugs or issues requiring human intervention).

Maintenance of the Indexer will involve:

*   Migrating and/or upgrading the Indexer for new open-source releases
*   Monitoring Bugsnag and Datadog for any issues and alerting internal team to address
*   Debugging and fixing any issues with a run book provided by dYdX

dYdX believes that, at minimum, a DevOps engineer will be required to perform the necessary duties for deployment and maintenance of the Indexer. An operator will need to utilize the services below:

*   AWS
    *   ECS - Fargate
    *   RDS - Postgres Database
    *   EC2
    *   Lambda
    *   ElastiCache Redis
    *   EC2 ELB - Loadbalancer
    *   Cloudwatch - Logs
    *   Secret Manager

*   Terraform Cloud - for deploying to the cloud
*   Bugsnag - bug awareness
*   Datadog - metrics and monitoring
*   Pagerduty - alerting

Operators should be able to host the open-sourced Indexer for public access in a highly available (i.e., high uptime) manner. Requirements include owning accounts to the services above and hiring the appropriate personnel to perform deployment and maintenance responsibilities.
Title: OEGS

URL Source: https://docs.dydx.xyz/concepts/architecture/oegs

Published Time: Tue, 14 Oct 2025 11:07:25 GMT

Markdown Content:
What is the Order Entry Gateway Service (OEGS)
----------------------------------------------

The Order Entry Gateway represents the next step in dYdX’s multi-stage performance evolution:

1.   Designated proposers — A governance-selected subset of validators responsible for proposing blocks. This creates a predictable topology for faster routing (available in v9 software upgrade).
2.   Order Entry Gateway Service (OEGS) — specialized nodes for direct, one-hop delivery to proposers (available after v9 upgrade).

The Order Entry Gateway Service (OEGS) is open-sourced infrastructure that provides a direct, optimized path from traders to the proposer set, reducing latency, increasing throughput, and lowering barriers for professional and retail traders alike. OEGS is now live on testnet, reach out to us for more information.

1. Previous State
-----------------

In dYdX previous architecture (original blog post [here](https://www.dydx.xyz/blog/v4-technical-architecture-overview)), orders from traders — whether via the web app, mobile, API, or third-party integration — are submitted to full nodes, which then gossip them across the network until they reach the current block proposer.

*   **Pros**: Fully decentralized, no single point of routing.

*   **Cons**: Multi-hop gossip introduces latency and unpredictability.

To achieve competitive speeds, professional trading firms have had to typically run their own private full nodes with streaming enabled, directly injecting orders into the gossip layer.

**Previous State** — orders flow through full nodes, then across an unpredictable set

### Validator and Full Node Roles

Validators drive consensus, maintain an off-chain in-memory order book, gossip transactions across the network, and propose blocks following a weighted round-robin proof of stake model.

Full Nodes run the same protocol software but hold no staking power—they don’t vote or propose. They gossip transactions, process committed blocks, and stream blockchain state to the Indexer—a read-optimized service that powers trading UIs with order book and trade data.

### Why Professional Traders run Full Nodes

Full-node access has become a performance necessity for high-speed trading — but it also represents a high barrier to entry—technical, financial, and operational.

Running a full node means orders don’t need to traverse geo-distributed public RPCs — you eliminate middle-hop latency by injecting them directly into the gossip network.

Full nodes also enable real-time streaming of L3 order book updates, fills, taker orders, and subaccount changes—via gRPC or WebSocket—supporting highly responsive UI or algorithmic trading logic.

Historically, traders relying solely on the public Indexer have faced reliability and uptime challenges, making self-hosted nodes the only way to guarantee consistent, low-latency market data. Since April 2025, we've made huge [improvements](https://x.com/AntonioMJuliano/status/1924593158165344628) (98%!) to API performance and reliability.

2. Designated Proposers
-----------------------

We recently introduced the concept of designated proposers (blog post [here](https://www.dydx.xyz/blog/governance-controlled-path-reliability-and-performance)) — a governance-selected subset of validators responsible for proposing blocks. This change to the open-source software creates a predictable topology, making it possible to route transactions directly to the next proposer instead of broadcasting widely. This is a fully deterministic enhancement to CometBFT that brings increased resilience, network performance, and operational clarity — while preserving the full validator set, stake-based voting power, and decentralized governance of the network.

3. The Order Entry Gateway Service (OEGS)
-----------------------------------------

The OEGS builds on the designated proposer model by creating a specialized set of gateway nodes that:

*   Peer directly with all designated proposers.
*   Accept orders via public, high-performance endpoints (gRPC).
*   Bypass standard gossip, broadcasting orders in a single hop to the proposer set.

This infrastructure built to:

*   Simplify access – traders can send orders to a public, high-performance gRPC endpoint instead of deploying their own nodes.
*   Ensure fairness – the Gateway peers directly with validator nodes, improving routing latency and propagation uniformity.
*   Scale gracefully – governance can update, expand, or delegate the Gateway set without disrupting overall network topology.

Gateway nodes streamline communication between traders and proposers, replacing the need for multiple gossip hops with direct and parallel message delivery.

![Image 1: OEGS](https://docs.dydx.xyz/OEGS.png)

How It Works: Infrastructure Flow
---------------------------------

1.   Trader submits an order via UI, API, or third-party partner integration to the OEGS.
2.   OEGS full nodes processes validation checks (similar to regular full node).
3.   Gateway is persistently peered with the proposer set—gossiping the order directly, bypassing standard gossip hops due to direct peering.
4.   Designated proposers include it in the next proposed block by consensus.
5.   Order fills are committed on-chain; full nodes and Indexers update their state accordingly.

This streamlined flow ensures minimal latency while preserving decentralization and consensus integrity.

### Deployment Options

dYdX Labs plans to fully open-source the OEGS code and infrastructure requirements. Any community deployed infrastructure (e.g., front-end, mobile app, API) could consider sending orders to the OEGS but this remains fully opt-in. Traders may still send orders directly to a full node which maintains decentralization and censorship-resistence. Governance may consider additional incentives for an OEGS operator, given their elevated role and service expectations.

### For Market Makers & Traders

You’ll get the benefit of ultra-low-latency order routing and immediate streaming data—without the burden of node deployment or uptime management. It levels the playing field between solo operators and well-resourced trading firms.

Getting Started
---------------

Head over to the OEGS endpoints [here](https://docs.dydx.xyz/interaction/endpoints) or take a look at the Node client Python example [here](https://docs.dydx.xyz/interaction/endpoints#node-client).

OEGS complements full-node streaming, validators’ performance, and indexer infrastructure. We’re planning further enhancements to scale alongside trader needs.
Title: Limit Order Book and Matching

URL Source: https://docs.dydx.xyz/concepts/trading/limit-orderbook

Markdown Content:
This document outlines the key differences between centralized exchanges and dYdX Chain, focusing on the decentralized limit order book and matching engine.

Blockchain Overview
-------------------

dYdX Chain is a p2p blockchain network using [CosmosSDK](https://github.com/cosmos/cosmos-sdk) and [CometBFT](https://github.com/cometbft/cometbft) (formerly Tendermint).

Anyone can run a full node using the open-source software. Full nodes with sufficient delegated governance tokens participate in block building as validators.

The software repository is: [https://github.com/dydxprotocol/v4-chain/](https://github.com/dydxprotocol/v4-chain/)

Each full node in the network maintains an in-memory order book, which undergoes state changes in real time as traders submit order instructions.

Block proposers use trades from their local order book to build blocks, with matches generated by price-time priority. Since message arrival order varies between nodes, the order book may differ across the network at any given point in time. To address this, upon seeing a new consensus-commited block, nodes sync their local books with the block contents.

Clients can subscribe to a node's book state using the [Full Node Streaming API](https://docs.dydx.xyz/nodes/full-node-streaming).

Matching and Block Processing
-----------------------------

The order matching logic is broadly similar to centralized exchanges, with some key differences:

1.   On receiving a cancel instruction:

    *   The node cancels the order unless it's already matched locally.
    *   The cancel instruction is stored until it expires (based on the [GTB field](https://github.com/dydxprotocol/v4-chain/blob/4780b4cba2cab75e0af5675c3e87e551162ecf33/proto/dydxprotocol/clob/tx.proto#L90)).

2.   On receiving an order:

    *   The order fails to place if it has already been cancelled.
    *   Otherwise, it is matched and/or placed on the order book, with optimistic matches stored locally.

3.   Validator nodes propose blocks that include all their local matches.

4.   When processing a new block:

    *   The node starts from the state of the prior block (local state used to propose is temporarily disregarded).
    *   The block’s changes are applied.
    *   The node replays its local state on top of the new state, during which:
        *   Cancels are preserved.
        *   Orders matched in the prior local state are re-placed.
        *   Orders may match differently, fail to place due to cancellation, or not match at all in the new state.

#### Source Code References

For further details on how the protocol handles these actions, refer to the following source code references:

*   See [here](https://github.com/dydxprotocol/v4-chain/blob/dc6e0a004fd81e3139a24f88b10605ab5ce16cfd/protocol/x/clob/ante/clob.go#L90) and [here](https://github.com/dydxprotocol/v4-chain/blob/2d5dfa55357abd5ead46f8baa03ed76d420849cc/protocol/x/clob/memclob/memclob.go#L103) for how the protocol reacts when (1) a cancel is seen.

*   When (2) [an order is placed](https://github.com/dydxprotocol/v4-chain/blob/dc6e0a004fd81e3139a24f88b10605ab5ce16cfd/protocol/x/clob/ante/clob.go#L132) and [checked to not be already cancelled](https://github.com/dydxprotocol/v4-chain/blob/749dff9cbca56eb2a6ab3a19feeb338de8db80e6/protocol/x/clob/keeper/orders.go#L780).

*   When (3) [proposing a block](https://github.com/dydxprotocol/v4-chain/blob/189b11217490aa5a87a4108dde0f679b0190511b/protocol/app/prepare/prepare_proposal.go#L157).

*   And (4) when [nodes process blocks committed by consensus](https://github.com/dydxprotocol/v4-chain/blob/4780b4cba2cab75e0af5675c3e87e551162ecf33/protocol/x/clob/abci.go#L152).

Order Messages
--------------

Order instructions are limit order placements, replacements, and cancellations.

> Note: This section covers short-term orders which live off-chain, in node memory, until matched.
> 
> 
> Stateful orders (on-chain, consensus-speed placement) exist for longer-lived limit orders but aren't recommended for API traders. More info: [Short-term vs Long-term Orders](https://docs.dydx.xyz/concepts/trading/orders#short-term-vs-long-term).

### Finality and GTB

Each limit order placement or cancellation [includes a GTB (good-til-block) field](https://github.com/dydxprotocol/v4-chain/blob/dc6e0a004fd81e3139a24f88b10605ab5ce16cfd/proto/dydxprotocol/clob/order.proto#L114-L146), which specifies the block height after which the instruction expires.

While rare, it is possible for a cancel instruction to be seen by the current block proposer but not by one or more subsequent proposers (if the instruction isn't gossiped to them in time through the p2p network). In such cases, the order could still match after the sender expects it to have been cancelled.

Therefore, we recommend that API traders consider setting tight GTB values on order placements (e.g. the current chain height + 3) because expiry due to GTB is the only guaranteed way for an order to become unfillable. Consensus does not permit any order to fill at a height greater than its GTB.

### Replacements

We recommend using replacement instructions over cancelling and placing new orders.

Replacing prevents accidental double-fills that can occur with a ‘place order A, cancel order A, place order B’ approach, where both A and B might fill simultaneously unless the chain height has already passed A’s GTB.

For example, after the following messages are sent:

1.   Place A: Sell 1 @ $100, client id = 123
2.   Cancel A
3.   Place B: Sell 1 @ $101, client id = 456

If a proposer sees messages 1 and 3, but not 2, it sees both orders A and B as open. If it also sees marketable bids for qty >= 2, both could fill simultaneously.

#### Replacement Instruction Fields

To replace an order, send a placement with the same order ID **and a larger GTB value**.

Orders have the same ID if these client-specified fields match ([OrderId proto definition](https://github.com/dydxprotocol/v4-chain/blob/dcd2d9c2f6170bd19218d92cf6f2f88216b2ffe1/proto/dydxprotocol/clob/order.proto#L9-L41)):

*   [Subaccount ID](https://github.com/dydxprotocol/v4-chain/blob/dcd2d9c2f6170bd19218d92cf6f2f88216b2ffe1/proto/dydxprotocol/subaccounts/subaccount.proto#L10-L17) (owner: signing address, number: 0 unless different subaccount)
*   Client ID
*   Order flags (0 for short-term orders)
*   CLOB pair ID
Title: Perpetuals and Assets

URL Source: https://docs.dydx.xyz/concepts/trading/assets

Markdown Content:
Perpetual contracts, or "perps," is a derivative and a type of futures contract commonly used in crypto trading. Unlike traditional futures, they do not have an expiration date, allowing traders to hold positions indefinitely. This makes them ideal for continuous speculation on asset prices.

### Benefits

*   Gain exposure to crypto prices without holding the actual tokens.
*   Go long or short depending on market expectations.
*   Hedge existing positions against volatility.
*   Potential for higher returns (with increased risk).
*   Earn from funding rate payments even when prices are stable.

### Risks

*   Falling below maintenance margin can lead to forced closure of positions.
*   High market swings can magnify losses, especially with leverage.
*   Requires understanding of derivatives mechanics (margin, funding, leverage).

Assets and Collateral
---------------------

To trade within dYdX, a collateral is required. Financially, a collateral is an asset that is pledged to secure a loan like borrowing cryptocurrency. In dYdX a collateral is used to:

*   Open and maintain trading positions;
*   Manage margin requirements;
*   Fee payments;
*   Other rewards.

Principal assets in dYdX are USDC and the dYdX token.
Title: Isolated Markets

URL Source: https://docs.dydx.xyz/concepts/trading/isolated-markets

Markdown Content:
In v5.0.0 the Isolated Markets feature was added to the V4 chain software. The below is an overview of how trading will work on Isolated Markets on the V4 chain software.

> Note: This document covers how the feature works from the protocol point of view and not the front end or the indexer. For more details on what isolated markets are see the [blog post](https://dydx.exchange/blog/introducing-isolated-markets-and-isolated-margin).

Positions in isolated markets can only be opened on a subaccount with no open perpetual positions or a subaccount with an existing perpetual position in the same isolated market. Once a perpetual position for an isolated market is opened on a subaccount, no positions in any other markets can be opened until the perpetual position is closed.

The above restriction only applies to positions, orders can still be placed for different markets on a subaccount while it holds an open position for an isolated market. The orders will fail and be canceled when they match if the subaccount still holds an open position for a different isolated market. A new [error code](https://github.com/dydxprotocol/v4-chain/blob/protocol/v5.0.0/protocol/x/clob/types/errors.go#L364-L368)`2005` has been added to indicate such a failure.

Other than the above caveat, isolated markets can be traded in the same way as before v5.0.0.

> Note: The maximum number of subaccounts per address was increased from 127 to 128000 in v5.0.0 to address the need for a separate subaccount per isolated market.

There is a new `market_type` parameter in the `PerpetualParams` proto struct that indicates the type of market.

There are 2 possible values for this parameter:

*   `PERPETUAL_MARKET_TYPE_CROSS` - markets where subaccounts can have positions cross-margined with other `PERPETUAL_MARKET_TYPE_CROSS` markets, all markets created before the v5.0.0 upgrade are `PERPETUAL_MARKET_TYPE_CROSS` markets
*   `PERPETUAL_MARKET_TYPE_ISOLATED` - markets that can only be margined in isolated, no cross-margining with other markets is possible

An example of how each type of market looks when queried using the `/dydxprotocol/perpetuals/perpetual/:id` REST endpoint.

*   `PERPETUAL_MARKET_TYPE_CROSS`

```
{
  "perpetual": {
    "params": {
      "id": 1,
      "ticker": "ETH-USD",
      "market_id": 1,
      "atomic_resolution": -9,
      "default_funding_ppm": 0,
      "liquidity_tier": 0,
      "market_type": "PERPETUAL_MARKET_TYPE_CROSS"
    },
    "funding_index": "0",
    "open_interest": "0"
  }
}
```

*   `PERPETUAL_MARKET_TYPE_ISOLATED`

```
{
  "perpetual": {
    "params": {
      "id": 1,
      "ticker": "FLOKI-USD",
      "market_id": 37,
      "atomic_resolution": -13,
      "default_funding_ppm": 0,
      "liquidity_tier": 2,
      "market_type": "PERPETUAL_MARKET_TYPE_ISOLATED"
    },
    "funding_index": "0",
    "open_interest": "0"
  }
}
```
Title: MegaVault

URL Source: https://docs.dydx.xyz/concepts/trading/megavault

Markdown Content:
MegaVault is a live feature on the dYdX that allows users to deposit **USDC** and earn yield by providing liquidity to various markets. It operates as an automated liquidity provisioning system, using deposited funds to run **automated market-making (AMM)** strategies across multiple trading pairs.

Depositors can contribute USDC at any time and begin earning yield immediately. Withdrawals are also supported, though factors such as market conditions, leverage, or open positions may affect the timing and value of withdrawals (via slippage). MegaVault is designed to benefit both sides of the protocol: users earn potential returns, and markets benefit from deeper liquidity and more efficient trading.

Yield for depositors can originate from:

*   Profit and loss (PnL) on market-making positions
*   A share of trading fees generated by the vault’s activity
*   Funding payments and incentives configured by governance or software deployers

An **operator**, elected through governance, currently manages certain manual operations like reallocating funds between sub-vaults and tuning quoting parameters. In future versions, these processes may be automated.

Vault Mechanics & User Experience
---------------------------------

*   **Sub-vault Architecture**: MegaVault is composed of multiple “sub-vaults,” each assigned to a specific market. When users deposit USDC, the funds are distributed among these sub-vaults based on liquidity needs. Each sub-vault runs its own AMM strategy, tailored for that market’s dynamics.

*   **Yield Aggregation & Distribution**: Returns generated from all sub-vaults are pooled and distributed proportionally among depositors. Users' deposits represent a fractional ownership of the vault’s total net equity — including both USDC and active trading positions.

*   **Deposits and Withdrawals**: Users can deposit USDC at any time with no minimums. Withdrawals are also available on-demand, but the amount received may be affected by the vault’s exposure and market volatility. This can result in **slippage** — especially during large withdrawals or volatile periods.

*   **Risks and Future Features**:

    *   Yield is **not guaranteed**. Depositors bear market risk, and negative PnL from trading positions can reduce vault equity.
    *   Withdrawals may be subject to **future restrictions**, such as **lockup periods** for specific strategies or new market listings.
    *   Currently, users cannot interact directly with sub-vaults; all deposits and withdrawals are routed through MegaVault.
upstream connect error or disconnect/reset before headers. reset reason: connection terminationTitle: Oracle Prices

URL Source: https://docs.dydx.xyz/concepts/trading/oracle

Markdown Content:
As part of the default settings of the v4 open source software (”dYdX Chain”), oracle prices are aggregated prices that provide up-to-date price data for different assets. The oracle price for each trading pair is used for the following:

*   Ensuring that each account is well-collateralized after each trade
*   Determining when an account should be liquidated
*   Triggering "triggerable" order types such as Stop-Limit and Take-Profit orders

How are oracle prices determined on dYdX Chain?
-----------------------------------------------

As part of the default settings on dYdX Chain, oracle prices will be determined by the current validator set of the network. In addition to verifying transactions and validating data, validators are also responsible for determining and verifying the oracle price. Once the oracle price is agreed upon during consensus, the oracle price is used to trigger “triggerable” order types such as Stop-Limit and Take-Profit orders.

How do validators agree on oracle price?
----------------------------------------

As part of the default settings on dYdX Chain, every validator would run a continuous process to calculate the fair market price for relevant assets. The block proposer suggests any needed price changes within the proposed blocks. Other validators then apply certain rules to agree on the prices in a manner that prevents misuse. If the block is accepted, the prices also get approved.

By following a new price-acceptance criteria, this logic helps validators make sure that the new suggested price is reasonable and not too far from both the previous referenced price. It ensures that sudden and extreme changes in the price are controlled and reasonable.

What happens if there is a sudden change in the Oracle price?
-------------------------------------------------------------

To prevent extreme fluctuations, validators apply rules to ensure that any suggested price changes are reasonable and not drastically different from previous prices. This helps maintain stability in the market.
Title: Quantums and Subticks

URL Source: https://docs.dydx.xyz/concepts/trading/quantums

Published Time: Tue, 14 Oct 2025 11:14:07 GMT

Markdown Content:
In dYdX, quantities and prices are represented in quantums (for quantities) and subticks (for prices), which need conversion for practical understanding.

The smallest increment of position size. Determined from `atomicResolution`.

atomicResolution - Determines the size of a quantum. [For example](https://github.com/dydxprotocol/v4-testnets/blob/aa1c7ac589d6699124942a66c2362acad2e6f50d/dydx-testnet-4/genesis.json#L5776), an `atomicResolution` of -10 for `BTC`, means that 1 quantum is `1e-10``BTC`.

Subticks
--------

Human-readable units: `USDC/<currency>` e.g. USDC/BTC

Units in V4 protocol: `quote quantums/base quantums` e.g. (`1e-14 USDC/1e-10 BTC`)

Determined by `quantum_conversion_exponent`, this allows for flexibility in the case that an asset’s prices plummet, since prices are represent in subticks, decreasing `subticks_per_tick` would allow for ticks to denote smaller increments between prices.

E.g. 1 `subtick` = `1e-14 USDC/1e-10 BTC` and if BTC was at 20,000 USDC/BTC, a `tick` being 100 USDC/BTC (`subtick_per_tick` = 10000) may make sense.

If BTC drops to 200 USDC/BTC, a `tick` being 100 USDC/BTC no longer makes sense, and we may want a `tick` to be 1 USDC/BTC, which lets us set `subtick_per_tick` to 100 to get to a `tick` size of 1 USDC/BTC.

Interpreting block data
-----------------------

![Image 1: Interpret1](https://docs.dydx.xyz/interpret_block_data_1.png)

### Buy or Sell

First, notice row I is negative. That means this trade is a sell by the taker account. If It was positive, it would be a buy.

### Market determination

Next, look at row N. The perpetual_id is 7, which maps to AVAX-USD market. You can see all the mappings from this endpoint for the dYdX Chain deployment by dYdX Operations Services Ltd. [https://indexer.dydx.trade/v4/perpetualMarkets](https://indexer.dydx.trade/v4/perpetualMarkets) where the clobPairId is the perpetual_id.

### Quantity determination

Next, we need to get the decimals for this market. First, get the atomicResolution from that endpoint above which we see is -7. Now we can get the size of the trade. From row I and J, take this number -500000000 and multiply by 10^(AtomicResolution) and you get: -500000000 x 10^-7 = 50, so the quantity is 50.

### Price determination

Next, look at row, E, F, G, H, I, and J

![Image 2: Interpret2](https://docs.dydx.xyz/interpret_block_data_2.png)

The price of the trade is either `abs((G+E)/I)*10e(-6 - AtomicResolution)`, or `abs((H+F)/J)*10e(-6 - AtomicResolution)`, either one is the same. Note that the ‘-6’ is because the AtomicResolution of USDC is -6.

`abs((1479130125 + 369875)/-500000000)*10e(-6 + 7) = 29.59`

`abs((-1479337255 - 162745)/500000000)*10e(-6 +7) = 29.59`

### Conclusion

In conclusion, we have determined that this trade is SELL 50 AVAX-USD at price $29.59
Title: Orders

URL Source: https://docs.dydx.xyz/concepts/trading/orders

Published Time: Tue, 14 Oct 2025 14:11:16 GMT

Markdown Content:
An order is the way a trader manages positions in the dYdX markets. Different types of orders exist to support different trading strategies.

Short-term vs Long-term
-----------------------

**Short-term** orders are short-lived orders that are not stored on-chain unless filled. These orders stay in-memory of the network validators, for up to 20 blocks, with only their fill amount and expiry block height being committed to state. Short-term orders are mainly intended for use by market makers with high throughput or for market orders.

**Long-term orders** are “stateful orders” that are committed to the blockchain. Long-term orders encompass any order that lives on the orderbook for longer than the short block window. The short block window represents the maximum number of blocks past the current block height that a short-term `MsgPlaceOrder` or `MsgCancelOrder` message will be considered valid by a validator. Currently the default short block window is 20 blocks.

### Comparison

|  | Short-term | Stateful |
| --- | --- | --- |
| purpose | Short-lived orders which are meant to placed immediately (in the same block the order was received). These orders stay in-memory up to 20 blocks, with only their fill amount and expiry block height being committed to state. Intended for use by market makers with high throughput, or for market orders. IoC and FoK orders are also considered short-term orders. Short-term orders do not survive a network restart. * • User would send a short-term transaction to a validator * • The transaction needs to contain exactly one Cosmos msg, and that msg is a [MsgPlaceOrder](https://github.com/dydxprotocol/v4-chain/blob/c092bf0166d1a111dcd9c2e4153334865c8fe553/proto/dydxprotocol/clob/tx.proto#L78) * • Each validator has a [MsgProposedOperations](https://github.com/dydxprotocol/v4-chain/blob/c092bf0166d1a111dcd9c2e4153334865c8fe553/proto/dydxprotocol/clob/tx.proto#L68), which is one validator’s view of the operations queue * • In the context of short-term orders, the block proposer should eventually be gossiped the short-term order and have it in their MsgProposedOperations * • The block proposer would then optimistically place the short-term order in [CheckTx](https://docs.cosmos.network/main/basics/tx-lifecycle) * • Matches that short term orders were included in block during MsgProposedOperations would be included in block for all the validators in the network during [DeliverTx](https://docs.cosmos.network/main/basics/tx-lifecycle) | Long-lived orders which may execute far in the future. These orders should not be lost during a validator restart (placed in the block after the order was received). In the event a validator restarts, all stateful orders are [placed back onto the in-memory orderbook](https://github.com/dydxprotocol/v4-chain/blob/95b59028af247c0a93ef72de9bfd09a645d30eb1/protocol/app/app.go#L1125). Likely to be used primarily by retail traders. The front end would be sending stateful orders for all order types other than market orders. Two types of stateful orders: 1. Long-Term Orders • meant to be added to the orderbook as soon as possible. Due to certain technical limitations, long-term orders are placed in the block after they are written to state. E.g. if `MsgPlaceOrder` is included in block N, taker order matching would occur for the long-term order in block N+1. • Order types requiring immediate execution such as fill-or-kill / immediate-or-cancel are disallowed as these should be placed as short term orders; Long-term FoK/IoC orders would never be maker orders, so there is no benefit to writing them to state. 2. Conditional Orders • execute when the oracle price becomes either LTE or GTE to specified trigger price, depending on the type of conditional order (e.g. stop loss sell = LTE, take profit buy = GTE) • orders are placed in the block after their condition is met and they become triggered • it is possible for a conditional order to become triggered in the same block they are initially written to state in. Conditional orders are placed in block ≥ N+1. |
| placement message | MsgPlaceOrder | `MsgPlaceOrder`, long term or conditional order flag enabled on `MsgPlaceOrder.Order.OrderId.OrderFlags` • valid OrderFlags values are 32 (conditional) and 64 (long-term) for stateful orders |
| cancellation message | MsgCancelOrder _Short term cancellations are handled best-effort, meaning they are only gossiped and not included in MsgProposedOperations_ | `MsgCancelOrder`, long term or conditional order flag enabled on `MsgCancelOrder.OrderId.OrderFlags` |
| expirations | Good-Till-Block (GTB) Short term orders have a maximum GTB of current block height + [ShortBlockWindow](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/protocol/x/clob/types/constants.go#L9). Currently this value is 20 blocks, or about 30 seconds. Short term orders can only be GTB because in the interest of being resilient to chain halts or slowdowns. | Good-Till-Block-Time (GTBT) Stateful orders have a maximum GTBT of current block time + [StatefulOrderTimeWindow](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/protocol/x/clob/types/constants.go#L17). Currently this value is 95 days. GTBT is used instead of GTB to give a more meaningful expiration time for stateful orders. |
| inclusion in block | `OperationRaw_ShortTermOrderPlacement` inside `MsgProposedOperations.OperationsQueue` which is an app-injected message in the proposal. Included if and only if the short term order is included in a match. | Normal cosmos transaction. The original Tx which included the `MsgPlaceOrder` or `MsgCancelOrder` would be included directly in the block. |
| signature verification | Short-term orders must undergo custom signature verification because they are included in an app-injected transaction. The memclob stores each short term order placement’s raw transaction bytes in the memclob. When the order is included in a match, an `OperationRaw_ShortTermOrderPlacement` operation is included in `MsgProposedOperations` which contains these bytes. During `DeliverTx`, we decode the raw transaction bytes into a transaction object and pass the transaction through the app’s antehandler which executes signature verification. If signature verification fails, the `MsgProposedOperations` execution returns an error and none of the operations are persisted to state. Operations for a given block is all-or-nothing, meaning all operations execute or none of them execute. | Normal cosmos transaction signature verification, executed by the app’s antehandler. |
| replay prevention | Keep orders in state until after Good-Till-Block aka expiry (even if fully-filled or cancelled) | Cosmos SDK sequence numbers, verified to be strictly increasing in the app’s antehandler. _Note that their use of sequence numbers requires stateful orders to be received in order otherwise they would fail. If placing multiple stateful orders they should be sent to the same validator to prevent issues._ |
| time placed (matching logic) | `CheckTx`, immediately after placement transaction is received by the validator. _Short term orders are only included in a block when matched. See “time added to state” below._ | long-term: Block N+1 in [PrepareCheckState](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/protocol/x/clob/abci.go#L136) where `MsgPlaceOrder` was included in block N conditional: Block N+1 `PrepareCheckState` where the order was triggered in `EndBlocker` of block N |
| what is stored in state | `OrderAmountFilledKeyPrefix`: • key = OrderId • value = OrderFillAmount & PrunableBlockHeight `BlockHeightToPotentiallyPrunableOrdersPrefix`: • key = block height • value = list of potentially prunable OrderIds PrunableBlockHeight holds the block height at which we can safely remove this order from state. BlockHeightToPotentiallyPrunableOrders stores a list of order ids which we can prune for a certain block height. These are used in conjunction for replay prevention of short term orders | `StatefulOrderPlacementKeyPrefix`: • key = OrderId • value = Order `StatefulOrdersTimeSlice`: • key = time • value = list of OrderIds expiring at this GTBT `OrderAmountFilledKeyPrefix`: • key = OrderId • value = OrderFillAmount & PrunableBlockHeight (prunable block height unused for stateful orders) |
| time added to state | `DeliverTx` when part of a match included in `MsgProposedOperations` | `StatefulOrderPlacementKeyPrefix` and `StatefulOrdersTimeSlice`: `DeliverTx`, the [MsgPlaceOrder](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/protocol/x/clob/keeper/msg_server_place_order.go#L22) is executed for `MsgPlaceOrder` msgs included in the block. The handler performs stateful validation, a collateralization check, and writes the order to state. _Stateful orders are also written to the checkState in CheckTx for spam mitigation purposes._ `OrderAmountFilledKeyPrefix`: DeliverTx, when part of a match included in `MsgProposedOperations` |
| time removed from state | Always in [EndBlocker](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/protocol/x/clob/abci.go#L60) based off of prunable block height | • cancelled by user: removed from state in `DeliverTx` for `MsgCancelOrder` • forcefully-cancelled by protocol: removed from state in `DeliverTx` when processing `OperationRaw_OrderRemoval` operation. This operation type is included by the proposer in `MsgProposedOperations` when a stateful order is no longer valid. Removal reasons listed [here](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/protocol/x/clob/types/order_removals.pb.go#L28) • fully-filled: removed from state in `DeliverTx` in the block in which they become fully filled. The order is added to `RemovedStatefulOrderIds` of `processProposerMatchesEvents` to be used in `EndBlocker` to remove from the in-memory orderbook. • expired: pruned during EndBlocker based off of GTBT _also removed from state in CheckTx for cancellations. This is for spam mitigation purposes._ |
| time added to in-memory orderbook | When placed in `CheckTx`, if not fully-matched | When placed in `PrepareCheckState`, if not fully-matched |
| time removed from in-memory orderbook | • when fully-filled: removed in `PrepareCheckState` where invalid memclob state is purged via fully filled orders present in `OrderIdsFilledInLastBlock` • when cancelled: (CheckTx) • when expired: PrepareCheckState, removed using memclob.openOrders.blockExpirationsForOrders data structure which stores expiration times for short term orders based off of GTB | • when fully-filled: removed in `PrepareCheckState` where we purge invalid memclob state based off of `RemovedStatefulOrderIds` • when cancelled: removed in `PrepareCheckState` based off of `PlacedStatefulCancellations` • when expired: removed in `PrepareCheckState` by `PurgeInvalidMemclobState`, using the list of `ExpiredStatefulOrderIds` produced in `EndBlocker` |

Types
-----

Currently, dYdX supports 6 different order types:

*   Market Order
*   Limit Order
*   Stop Market Order
*   Stop Limit Order
*   Take Profit Market Order
*   Take Profit Limit Order

### Market Order

A Market Order is an order to buy or sell a given asset and will execute immediately at the best price dependent on the liquidity on the other side of the order book. By default, the front end submits market orders as Immediate-or-Cancel orders, meaning the order will fill immediately (matched against the other side of the order book) and any part that isn’t filled will be canceled. Market orders are also used to close positions. For closing positions, the order is submitted as an Immediate-or-Cancel order.

### Limit Order

A Limit Order is an order to buy or sell a given asset at a specified (or better) price. A limit order to buy will only execute at the limit price or lower, and a limit order to sell will only execute at the limit price or higher.

### Stop Market Order

A Stop Market Order protects against losses by closing a trader’s position once the Oracle Price or the last traded price* crosses the trigger price. The trigger price can be triggered by either the Oracle Price or the last traded price*. Stop market orders can be used to limit losses on a trader’s positions by automatically closing them when the price falls below (for longs) or rises above (for shorts) the trigger price.

Once triggered, the resulting market order will be immediately filled at the best price on the books.

### Stop Limit Order

A Stop Limit Order will execute only when the Oracle Price or the last traded price* crosses a specified Trigger Price. The trigger price can be triggered by either the Oracle Price or the last traded price*. Stop limit orders can be used to limit losses on a trader’s positions by automatically closing them when the price falls below (for longs) or rises above (for shorts) the trigger price.

Once triggered, the resulting limit order may either be immediately filled or may rest on the orderbook at the limit price. The limit price operates exactly the same as for normal limit orders.

### Take Profit Market Order

Take Profit Market orders allow traders to set targets and protect profits on positions by specifying a price at which to close an open position for profit. Take profit market orders lock in profits by closing a trader’s position once the Oracle Price or last traded price* crosses the trigger price.

For a long position, a trader places a stop above the current market price. For a short position, a trader places the stop below the current market price. Stop limit orders can be used to limit losses on a trader’s positions by automatically closing them when the price falls below (for longs) or rises above (for shorts) the trigger price.

### Take Profit Limit Order

Take Profit Limit orders allow traders to set targets and protect profits on positions by specifying a price at which to close an open position for profit. Take profit limit orders enable profit taking like take profit market orders, but with the versatility and control of a limit order.

For a long position, a trader places a take profit limit above the current market price. For a short position, a trader places the trigger below the current market price. If the Oracle Price or last traded price* rises/drops to take-profit point, the T/P order changes from 'Untriggered' -> 'Open', and then behaves as a traditional limit order. Take-profit orders are best used by short-term traders interested in managing their risk. This is because they can get out of a trade as soon as their planned profit target is reached and not risk a possible future downturn in the market.

### TWAP Orders (release in v9.0)

TWAP (Time weighted average price) orders enable users to submit orders that will be executed at certain time intervals at the current market price.
Title: Margining

URL Source: https://docs.dydx.xyz/concepts/trading/margin

Published Time: Tue, 14 Oct 2025 12:03:18 GMT

Markdown Content:
As part of default settings on the dYdX Chain open source software, each market has two risk parameters, Initial Margin Fraction (IMF) and Maintenance Margin Fraction (MMF):

*   **Initial Margin Fraction**: A percentage (fixed until [certain level](https://docs.dydx.xyz/concepts/trading/margin#open-interest-based-imf) of Open Interest) that determines the minimum collateral required to open or increase positions.

*   **Maintenance Margin Fraction**: A percentage (fixed) that determines the minimum collateral required to maintain positions and avoid liquidation.

Open-Interest-Based IMF
-----------------------

The IMF of a perpetual market scales linearly according to the current `open_notional` in the market, starting at `open_notional_lower_cap` to `open_notional_upper_cap` (USDC denominated):

```
open_notional = open_interest * oracle_price
 
scaling_factor = (open_notional - open_notional_lower_cap) / (open_notional_upper_cap - open_notional_lower_cap)
 
IMF_increase = scaling_factor * (1 - base_IMF)
 
effective_IMF = Min(base_IMF + Max(IMF_increase, 0), 100%)
```

I.e. the effective IMF is the base IMF while `open_notinal < lower_cap`, and increases linearly until `open_notional = upper_cap`, at which point the IMF stays at 100% (requiring 1:1 collateral for trading). Importantly, the MMF (Maintenance Margin Fraction) does not change.

The [Open Notional Lower Cap](https://github.com/dydxprotocol/v4-chain/blob/b829b28b0d71e754ac553fbeec29ce5309bd79f7/proto/dydxprotocol/perpetuals/perpetual.proto#L133) and [Open Notional Upper Cap](https://github.com/dydxprotocol/v4-chain/blob/b829b28b0d71e754ac553fbeec29ce5309bd79f7/proto/dydxprotocol/perpetuals/perpetual.proto#L138) are parameters defined as part of the market's [Liquidity Tier](https://github.com/dydxprotocol/v4-chain/blob/b829b28b0d71e754ac553fbeec29ce5309bd79f7/proto/dydxprotocol/perpetuals/perpetual.proto#L100).

Margin Calculation
------------------

The margin requirement for a single position is calculated as follows:

Initial Margin Requirement = abs(S × P × I) Maintenance Margin Requirement = abs(S × P × M)

Where:

*   `S` is the size of the position (positive if long, negative if short)
*   `P` is the oracle price for the market
*   `I` is the initial margin fraction for the market
*   `M` is the maintenance margin fraction for the market

The margin requirement for the account as a whole is the sum of the margin requirement over each market `i` in which the account holds a position:

Total Initial Margin Requirement = Σ abs(S i × P i × I i) Total Maintenance Margin Requirement = Σ abs(S i × P i × M i)

The total margin requirement is compared against the total value of the account, which incorporates the quote asset (USDC) balance of the account as well as the value of the positions held by the account:

Total Account Value = Q + Σ (S i × P i)

The Total Account Value is also referred to as equity.

Where:

*   `Q` is the account's USDC balance (note that `Q` may be negative). In the API, this is called `quoteBalance`. Every time a transfer, deposit or withdrawal occurs for an account, the balance changes. Also, when a position is modified for an account, the `quoteBalance` changes. Also funding payments and liquidations will change an account's `quoteBalance`.
*   `S` and `P` are as defined above (note that `S` may be negative)

An account cannot open new positions or increase the size of existing positions if it would lead the total account value of the account to drop below the total initial margin requirement. If the total account value ever falls below the total maintenance margin requirement, the account may be liquidated.

Free collateral is calculated as:

Free collateral = Total Account Value - Total Initial Margin Requirement

Equity and free collateral can be tracked over time using the latest oracle price (obtained from the markets websocket).
Title: Funding

URL Source: https://docs.dydx.xyz/concepts/trading/funding

Published Time: Tue, 21 Oct 2025 11:49:57 GMT

Markdown Content:
What are funding rates?
-----------------------

Perpetual contracts have no expiry date and therefore no final settlement or delivery. Funding payments are therefore used to incentivize the price of the perpetual to trade at the price of the underlying.

The purpose of the funding rate is to keep the price of each perpetual market trading close to its Oracle Price. When the price is too high, longs pay shorts, incentivizing more traders to sell / go short, and driving the price down. When the price is too low, shorts pay longs, incentivizing more traders to buy / go long, driving the price up.

How are funding rates calculated on dYdX ?
------------------------------------------

The main component of the funding rate is a premium that considers market activity for a perpetual. It is calculated for every market using the formula:

`Premium = (Max(0, Impact Bid Price - Index Price) - Max(0, Index Price - Impact Ask Price)) / Index Price`

Where the impact bid and impact ask prices are defined as:

*   `Impact Bid Price` = Average execution price for a market sell of the impact notional value
*   `Impact Ask Price` = Average execution price for a market buy of the impact notional value
*   `Impact Notional Amount = 500 USDC / Initial Margin Fraction`

For example, at a 10% initial margin fraction, the impact notional value is 5,000 USDC. At the end of each hour, the one-hour premium is calculated as the simple average (i.e. TWAP) of the 60 premiums calculated over the last hour.

How is the sample calculated?

At a high level, the proposer determines the premium for each block based on their local view of the order book and then proposes a `FundingPremiumVote`. At the end of each `funding-sample` period (default to 1 minute), the median `FundingPremiumVote` is taken as the sample for that period. Therefore, at the end of each `funding-tick` period (default to 1 hour), the average of the past samples is used as the final funding rate.

In addition to the premium component, each market has a fixed interest rate component that aims to account for the difference in interest rates of the base and quote currencies. The funding rate is then:

`Funding Rate = (Premium Component / 8) + Interest Rate Component`

As part of the default settings of the v4 open source software, the interest rate component for cross markets is 0% . The funding rate is simply the one-hour premium for markets with no interest rate component. As part of [governance vote 220](https://dydx.forum/t/drc-update-default-funding-rate-for-isolated-markets/3417) the default interest rate component for isolated markets is 0.125 bps per hour or 1 bps per 8 hours.

What role do block proposers play in funding rates on dYdX?
-----------------------------------------------------------

As part of the default settings of the v4 open source software, there are two distinct epochs established with the Epochs module. Every block proposer proposes a `FundingPremiumVote` during each block. At the end of a `funding-sample` epoch, the state machine deterministically computes a funding sample from all the `FundingPremiumVote`s in this epoch (1 minute).

The second epoch is the "funding-tick epoch," which occurs every hour at the start of the hour and is responsible for adjusting funding rates based on the funding samples collected from the preceding epoch.

Where is the funding rate for a particular market located on dYdX?
------------------------------------------------------------------

Please see the [Get Historical Funding](https://docs.dydx.xyz/indexer-client/http#get-historical-funding) API method.

What is a funding rate cap?
---------------------------

The funding rate cap refers to a predetermined maximum limit on the funding rate applied to a particular contract. It aims to limit the potential costs incurred by traders, especially during volatile market conditions. As part of the default settings of the v4 open source software, there’s a cap on each funding sample (per minute) and the funding rate (per hour).

How is the funding rate cap calculated?
---------------------------------------

The 8-hour rate cap is calculated by `600% * (Initial Margin - Maintenance Margin)`.

| Market | Initial margin | Maintenance margin |
| --- | --- | --- |
| Large-Cap | 5% | 3% |
| Mid-Cap | 10% | 5% |
| Long-Tail | 20% | 10% |

For example, for BTC-USD, which falls under Large-Cap, the 8-hour rate is capped by `600% * (IMF - MMF) = 600% * (5% - 3%) = 12%`.

FAQ
---

> What Funding parameters can be controlled by Governance?

Governance has the ability to adjust Funding Rate parameters:

*   Funding rate clamp factor, premium vote clamp factor, and min number of votes per premium sample. Proto
*   Epoch information, which defines the funding interval and premium sampling interval. Proto
*   Liquidity Tier, which defines the impact notional value. Proto

> How does the funding rate impact P&L?

Realized P&L increases or decreases while you hold a position due to funding fees, which are paid or received every hour depending on your position and the funding rate.

> When are the funding rates charged?

We charge funding rates every hour on our platform. The funding rate is calculated at the end of each hour and is based on the average of premiums collected over the last 60 minutes. This hourly funding rate helps keep the perpetual contract prices aligned with their underlying asset prices.

> Where can I find the details of how much I paid for the funding rate and view my payment history?

Funding rate payments are reflected in the "Funding" section of your account history on the dYdX frontend. You can also view your funding rate payment history through the [Get Funding History](https://docs.dydx.xyz/indexer-client/http#get-funding-payments) API method.
Title: Liquidations

URL Source: https://docs.dydx.xyz/concepts/trading/liquidations

Markdown Content:
As part of the default settings of the v4 open source software (”dYdX Chain”), accounts whose total value falls below their maintenance margin requirement may have their positions automatically closed by the liquidation engine. Positions are closed via protocol-generated liquidation matches where a protocol-generated liquidation order uses a calculated “Fillable Price” as the limit price to match against liquidity resting on the order book.

Profits or losses from liquidations are taken on by the insurance fund. A liquidated subaccount may have its position partially or fully closed. v4 open source software includes a liquidations configuration which — as determined by the applicable Governance Community — will determine how much of the position is liquidated.

Liquidation Penalty
-------------------

As part of the default settings of the v4 open source software, when an account is liquidated, up to the entire remaining value of the account may be taken as penalty and transferred to an insurance fund.

The liquidation engine will attempt to leave funds in accounts of positive value where possible after they have paid the Maximum Liquidation Penalty of 1.5%. The 1.5% fee contemplated in the default v4 software will be subject to adjustments by the applicable Governance Community.

Isolated Liquidation Price
--------------------------

This is the price at which a specific position reaches the point of liquidation.

1.   **Formula Explanation:**

*   The liquidation price `p'` is calculated using:

`p' = (e - s * p) / (|s| * MMF - s)`

*   Here:
    *   `e` is the current equity in the account.
    *   `s` is the size of the position.
    *   `p` is the original price of the position.
    *   `MMF` is the maintenance margin fraction, a percentage that indicates the minimum equity required to keep the position open.

1.   **Example:**

*   Suppose a trader deposits $1,000 (`e = 1000`).
*   The trader shorts 3 ETH contracts (`s = -3`) at $3,000 per contract, with a maintenance margin fraction of 5% (`MMF = 0.05`).
*   The formula becomes: `p' = (1000 - (-3 * 3000)) / (3 * 0.05 - (-3))`
*   This simplifies to: `p' = (1000 + 9000) / (0.15 + 3) = 10000 / 3.15 ≈ 3174.60`
*   This means if the price of ETH rises to $3,174.60, the position will reach the liquidation threshold.
*   At this price, the trader's remaining equity would be 5% of the notional value of the position or $476.2 based on the calculation `(3 * 3174.6 * 0.05 ≈ 476.2)`.

Cross Liquidation Price
-----------------------

For cross-margining (multiple positions sharing the same margin), the calculation is adjusted to account for the margin used by other positions.

1.   **Key Terms:**

*   **Total Maintenance Margin Requirement (`MMR_t`):** Calculate the maintenance margin needed for all positions at current prices: `MMR_t = |s| · p · MMF`
*   **Other Positions' Margin Requirement (`MMR_o`)**: Subtract the margin requirement of the position in question from MMR_t: `MMR_o = MMR_t - |s| * p * MMF`
*   **New Margin Requirement at Price `p'`**: Add `MMR_o` to the margin requirement of the position at the new price: `MMR_o + |s| * p' * MMF`
*   **Liquidation Price Formula**: Substitute into the equation to find the liquidation price for the position: `p' = (e - s * p - MMR_o) / (|s| * MMF - s)`

1.   **Example:**

*   Suppose a trader deposits $1,000 (`e = 1000`).
*   The trader shorts 1.5 ETH (`s = -1.5`) at $3,000 and buys 1,000 STRK contracts at $1.75 (`MMF = 10%` for STRK).
*   **Calculate Other Positions' Margin Requirement**: `MMR_o = 1000 * 1.75 * 0.10 = 175`
*   Compute the Liquidation Price for ETH: `p' = (1000 - (-1.5 * 3000) - 175) / (1.5 * 0.05 + 1.5)`
*   This simplifies to: `p' = (1000 + 4500 - 175) / 1.575 ≈ 3380.95`.
*   If the ETH price reaches $3,380.95, the equity would fall to the required margin level.

“Fillable Price” for Liquidations
---------------------------------

As part of the default settings of dYdX Chain, the “fillable price” (or the limit price of a liquidation order) for a position being liquidated is calculated as follows. For both short and long position:

`Fillable Price (Short or Long) = P x (1 - ((SMMR x MMF) x (BA x (1 - Q)))`

Where (provided as genesis parameters):

*   `P` is the oracle price for the market
*   `SMMR` is the spread to maintenance margin ratio
*   `MMR`= `Config.FillablePriceConfig.SpreadToMaintenanceMarginRatioPpm`
*   `MMF` is the maintenance margin fraction for the position
*   `BA` is the bankruptcy adjustment
*   `A` = `Config.FillablePriceConfig.BankruptcyAdjustmentPpm`. Is ≥ 1.
*   `Q = V / TMMR` where `V` is the total account value, and `TMMR` is the total maintenance margin requirement

On the other hand, the “Close Price” will be the sub-ticks of whatever maker order(s) the liquidation order matches against.

For more information on Margin fractions and calculations, see [Margin](https://docs.dydx.xyz/concepts/trading/margin).

FAQ
---

> What price is used to determine liquidations?

As part of the default settings, Oracle Price is used to estimate the value of an account’s positions. If the account’s value falls below the account’s maintenance margin requirement, the account is liquidatable.

> Who receives the liquidation fees?

The insurance fund would receive liquidation fees / penalty. Please note that the applicable Governance Community needs to initially fund the insurance fund from the applicable community treasury.

> How liquidation engine works?

Our liquidation engine automatically closes positions that fall below the maintenance margin.

> Does dYdX apply a penalty in the event of liquidation?

Yes. The liquidation engine will attempt to leave funds in accounts of positive value where possible after they have paid the Maximum Liquidation Penalty of 1.5%. The 1.5% fee contemplated in the default v4 software will be subject to adjustments by the applicable Governance Community.

> How to avoid liquidation?

In order to avoid liquidation, you can deposit more assets to your account, as while opening a position the key point is to have enough assets to cover the maintenance margin requirements. You can also close the part of the position and the liquidation price will change.
Title: Accounts and Subaccounts

URL Source: https://docs.dydx.xyz/concepts/trading/accounts

Markdown Content:
Accounts and subaccounts serve as identifiers in the dYdX ecosystem.

Main Account
------------

A (main) account is associated with a public-private keypair, and with a trader's on-chain identity.

*   Known publicly and associated with an address;
*   Holds tokens/assets that are sent to/from the chain, including tokens used for gas and collateral;
*   Gas for transactions is used from the main account;
*   Main accounts cannot trade;
*   Several main accounts can be derived from the same mnemonic phrase. Each user main account is completely independent and private/unlinkable from each other.

Subaccounts provide a way to isolate funds and manage risk within an account. They are used to trade.

*   Each main account can have 128,001 subaccounts;
*   Each subaccount is uniquely identified using as subaccount ID of `(main account address, integer)`;
*   Once you deposit funds to a valid subaccount ID, the subaccount will automatically be created;
*   Only the main account can send transactions on behalf of a subaccount;
*   Subaccounts do not require gas (no gas is used for trading);
*   Subaccounts require collateral token (currently USDC) in order to trade.
Title: Isolated Positions

URL Source: https://docs.dydx.xyz/concepts/trading/isolated-positions

Markdown Content:
Isolated Positions – dYdX Documentation

===============

[Skip to content](https://docs.dydx.xyz/concepts/trading/isolated-positions#vocs-content)

[![Image 1: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Guide

API

Concepts

Architecture

Trading

[Limit Orderbook and Matching](https://docs.dydx.xyz/concepts/trading/limit-orderbook)

Markets

Account Operations

[Orders](https://docs.dydx.xyz/concepts/trading/orders)[Margin](https://docs.dydx.xyz/concepts/trading/margin)[Funding](https://docs.dydx.xyz/concepts/trading/funding)[Liquidations](https://docs.dydx.xyz/concepts/trading/liquidations)[Accounts and Subaccounts](https://docs.dydx.xyz/concepts/trading/accounts)[Isolated Positions](https://docs.dydx.xyz/concepts/trading/isolated-positions)[Permissioned Keys](https://docs.dydx.xyz/concepts/trading/authenticators)

Rewards, Fees and Limits

[Onboarding FAQs](https://docs.dydx.xyz/concepts/onboarding-faqs)

Nodes

Policies

Search...

[![Image 2: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

[![Image 3: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Menu

Isolated Positions

On this page

[Ask in ChatGPT](https://chatgpt.com/?hints=search&q=Please%20research%20and%20analyze%20this%20page%3A%20https%3A%2F%2Fdocs.dydx.xyz%2Fconcepts%2Ftrading%2Fisolated-positions%20so%20I%20can%20ask%20you%20questions%20about%20it.%20Once%20you%20have%20read%20it%2C%20prompt%20me%20with%20any%20questions%20I%20have.%20Do%20not%20post%20content%20from%20the%20page%20in%20your%20response.%20Any%20of%20my%20follow%20up%20questions%20must%20reference%20the%20site%20I%20gave%20you.)

On this page
------------

*   [Mapping of isolated positions to subaccounts](https://docs.dydx.xyz/concepts/trading/isolated-positions#mapping-of-isolated-positions-to-subaccounts)

    *   [Parent subaccounts](https://docs.dydx.xyz/concepts/trading/isolated-positions#parent-subaccounts)
    *   [Child subaccounts](https://docs.dydx.xyz/concepts/trading/isolated-positions#child-subaccounts)

*   [Getting data for parent subaccount](https://docs.dydx.xyz/concepts/trading/isolated-positions#getting-data-for-parent-subaccount)

Isolated Positions[](https://docs.dydx.xyz/concepts/trading/isolated-positions#isolated-positions)
==================================================================================================

**Isolated positions** on the **dYdX frontend** are perpetual positions held in subaccounts with a subaccount number greater than 127, up to the limit of 128,000. Each isolated position is held in a separate subaccount.

**Isolated positions** are a feature provided and managed by the **dYdX frontend** (web) interface. This page provides information on how to integrate this feature into your API-based implementation.

Mapping of isolated positions to subaccounts[](https://docs.dydx.xyz/concepts/trading/isolated-positions#mapping-of-isolated-positions-to-subaccounts)
------------------------------------------------------------------------------------------------------------------------------------------------------

The dYdX frontend implementation separates subaccounts (0 - 128,000) into 2 separate types.

### Parent subaccounts[](https://docs.dydx.xyz/concepts/trading/isolated-positions#parent-subaccounts)

Subaccounts 0 to 127 are parent subaccounts. Parent subaccounts can have multiple positions opened and all positions are cross-margined.

### Child subaccounts[](https://docs.dydx.xyz/concepts/trading/isolated-positions#child-subaccounts)

Subaccounts 128 to 128,000 are child subaccounts. Child subaccounts will only ever have up to 1 position open. Each open isolated position on the frontend is held by a separate child subaccount. Once an isolated position is closed in the frontend, the subaccount associated with isolated position can be re-used for the next isolated position.

Child subaccounts are mapped to parent subaccounts using the formula: e.g. parent subaccount 0 has child subaccounts 128, 256,... parent subaccount 1 has child subaccounts 129, 257,...

`parent_subaccount_number = child_subaccount_number % 128`

Note that currently only parent subaccount 0 is exposed via the frontend and so isolated positions will be held in subaccounts number 128, 256, ...

Note that the above "types" of subaccounts are not enforced at a protocol level, and only on the frontend. Any subaccount can hold any number of positions in cross-marginable markets which all will cross-margined at the protocol level.

When you are using the dYdX frontend, any margin transferred to an empty child subaccount that isn’t used for placing a trade will get sent back to the cross subaccount after some time.

Getting data for parent subaccount[](https://docs.dydx.xyz/concepts/trading/isolated-positions#getting-data-for-parent-subaccount)
----------------------------------------------------------------------------------------------------------------------------------

API endpoints exist to get data for a parent subaccount and all it's child subaccounts on the Indexer.

> Currently all data for an account viewable on the frontend can be fetched by using the parent subaccount APIs to fetch data for parent subaccount number 0.

See the [Indexer API](https://docs.dydx.xyz/indexer-client/http#get-parent-subaccount) page for more details of the parent subaccount APIs.

Last updated: 9/19/25, 5:57 AM

[Accounts and Subaccounts Previous shift←](https://docs.dydx.xyz/concepts/trading/accounts)[Permissioned Keys Next shift→](https://docs.dydx.xyz/concepts/trading/authenticators)
Title: Permissioned Keys

URL Source: https://docs.dydx.xyz/concepts/trading/authenticators

Markdown Content:
Overview
--------

Permissioned Keys are a dYdX specific extension to the Cosmos authentication system that allows an account to add custom logic for verifying and confirming transactions placed on that account. For example, an account could enable other accounts to sign and place transactions on their behalf, limit those transactions to certain message types or clob pairs etc, all in a composable way.

To enable this there are currently six types of "authenticator" that can used, four that enable specific authentication methods and two that allow for composability:

**Sub-Authenticator Types**
*   **SignatureVerification**– Enables authentication via a specific key
*   **MessageFilter**– Restricts authentication to certain message types
*   **SubaccountFilter**– Restricts authentication to certain subaccount constraints
*   **ClobPairIdFilter**– Restricts transactions to specific CLOB pair IDs

**Composable Authenticators**
*   **AnyOf**- Succeeds if _any_ of its sub-authenticators succeeds
*   **AllOf**- Succeeds only if _all_ sub-authenticators succeed

Capabilities
------------

### Available Features ✅

1.   **Account Access Control**
    *   Limit withdrawals/transfers entirely
    *   Multiple trading keys under same account
    *   Trading key separation from withdrawal keys

2.   **Asset-Specific Trading**
    *   Whitelist specific trading pairs
    *   E.g., Allow BTC/USD and ETH/USD, restrict others

3.   **Subaccount Management**
    *   Control trading permissions per subaccount
    *   E.g., Enable trading on subaccount 0, restrict subaccount 1

### Current Limitations ❌

1.   **Position Management**
    *   Cannot set maximum position sizes
    *   No order size restrictions
    *   No custom leverage limits
Title: Rewards, Fees and Parameters

URL Source: https://docs.dydx.xyz/concepts/trading/rewards

Markdown Content:
There are several reward mechanisms available with the protocol software.

![Image 1: Rewards Overview](https://docs.dydx.xyz/rewards_overview.png)

|  | Target Users | Rewards paid in | Claim Process | Frequency |
| --- | --- | --- | --- | --- |
| Staking Rewards | Validators & Stakers | USDC & NATIVE_TOKEN | Manual | Per Block |
| Trading Rewards | Traders | NATIVE_TOKEN | Automatic | Per Block (with trades) |

Staking Rewards
---------------

*   Rewards distributed to `Validators` and `Stakers` (= Delegators)
*   `Staking Rewards = Trading Fees + Gas Fees - Community Tax - Validator Commission`
*   Distributed automatically every block
*   Must be claimed manually

See more on [Staking Rewards](https://docs.dydx.xyz/concepts/trading/rewards/staking-rewards).

Trading Rewards (Note that C factor has been set to 0)
------------------------------------------------------

*   Rewards distributed to `Traders` after each successful trade
*   Based on a specified `formula` with several inputs
*   Distributed automatically every block with successful trades
*   Claimed automatically

See more on [Trading Rewards](https://docs.dydx.xyz/concepts/trading/rewards/trading-rewards).

Fees
----

_The fee schedule is subject to adjustments by the applicable Governance Community_

The basic structure for fees have been developed to reflect the following characteristics:

1.   Fees differ based on side (maker/taker)
2.   Users are eligible for lower fees based on their 30 day trading volume across sub accounts and markets
3.   Fees are uniform across all markets

| Tier | 30d Trailing Volume | Taker (bps) | Maker (bps) | Effective Taker Fee (FE) | Effective Maker Fee (FE) | Effective Taker Fee (API) | Effective Maker Fee (API) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | < $1M | 5.0 | 1.0 | 0 | 0 | 2.5 | 0.5 |
| 2 | ≥ $1M | 4.5 | 1.0 | 0 | 0 | 2.25 | 0.5 |
| 3 | ≥ $5M | 4.0 | 0.5 | 0 | 0 | 2.0 | 0.25 |
| 4 | ≥ $25M | 3.5 | 0 | 0 | 0 | 1.75 | 0 |
| 5 | ≥ $50M | 3.0 | 0 | 0 | 0 | 1.5 | 0 |
| 6 | ≥ $100M | 2.5 | -0.7 | 0 | -0.7 | 1.25 | -0.7 |
| 7 | ≥ $200M | 2.5 | -1.1 | 0 | -1.1 | 1.25 | -1.1 |

Parameters
----------

_Below is a summary of various notable parameters and what they mean for any chain utilizing the open source software. Parameters will be subject to adjustments by the applicable Governance Community and can be set to different values at Genesis by any deployer._

**Bank Parameters**
This parameter establishes whether transfers for any tokens are enabled at Genesis. Transfers will be enabled.

**State Parameters**
The open source software will not pre-populate any bank-state on the network. Validators who participate in Genesis have the ability to determine the network’s initialized state.

**Slashing Parameters**
These parameters establish punishments for detrimental behavior by validators.

|  | Signed Blocks Window | Min Signed Per Window | Downtime Jail Duration | Slash Fraction Doublesign | Slash Fraction Downtime |
| --- | --- | --- | --- | --- | --- |
| Slashing Params | 8192 (-3 hrs) | 20% | 7200s | 0% | 0% |

_SignedBlocksWindow_: Together with MinSignedPerWindow, specifies the number of blocks a validator must sign within a sliding window. Failure to maintain MinSignedPerWindow leads to validator being jailed (removed from active validator set).

_SlashFractionDownTime_: Defines the slashing-penalty for downtime

_DownTimeJailDuration_: How long before the validator can unjail themselves after being jailed for downtime.

Double-signing by a validator is considered a severe violation as it can cause instability and unpredictability in the network. When a validator double-signs, they are slashed for SlashFractionDoubleSign, jailed (removed from validator set) and tombstoned (cannot rejoin validator set).

**Distribution Parameters**
These parameters handle the distribution of gas and trading fees generated by the network to validators.

|  | Community Tax | WithdrawAddrEnable |
| --- | --- | --- |
| Distribution Params | 0% | True |

_CommunityTax_: Fraction of fees that goes to the community treasury. The software will initially reflect a 0% community tax.

_WithdrawAddrEnabled_: Whether a delegator can set a different withdrawal address (other than their delegator address) for their rewards.

**Staking Parameters**
These parameters define how staking works on the protocol and norms around staking.

*MaxValidators and UnbondingTime are particularly subject to change based on public testnet data and feedback.

|  | BondDenom | MaxValidators | MinCommissionRate | Unbonding Time |
| --- | --- | --- | --- | --- |
| Slashing Params | Decided at Genesis, by validators | 60 | 5% | 30 days |

_MaxValidators_: Every block, the top MaxValidators validators by stake weight are included in the active validator set.

_UnbondingTime_: Specifies the duration of the unbonding process, during which tokens are in a locked state and cannot be transferred or delegated (the tokens are still “at stake”).

_MinCommissionRate_: The chain-wide minimum commission rate that a validator can charge their delegators. The default commission rate will be 100%.

**Governance Parameters**
These parameters define how governance proposals can be submitted and executed. For more information on the governance module and its associated parameters, head to the official [Cosmos SDK docs](https://docs.cosmos.network/v0.47/modules/gov#parameters).

|  | Min Deposit | MinInitialDepositRatio | Max Deposit Period | Voting Period | Quorum | Threshold | Veto |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gov Params | 10,000 governance token | 20% | 1 Days | 4 Days | 33.4% | 50% | 33.4% |
Title: Staking Rewards

URL Source: https://docs.dydx.xyz/concepts/trading/rewards/staking-rewards

Markdown Content:
Staking rewards are designed to reward `Validators` and `Stakers` (=Delegators). The sources of staking rewards are trading fees and gas fees collected by the protocol.

The protocol uses the [CosmosSDK’s x/distribution module](https://docs.cosmos.network/main/build/modules/distribution) to allocate the accrued trading and gas fees to `Validators` and `Stakers`.

![Image 1: Staking Rewards](https://docs.dydx.xyz/staking_rewards.png)

All trading fees (`USDC`) and gas fees (`USDC` and `NATIVE_TOKEN`) collected by the protocol are accrued and distributed within a block. Specifically — for each block, the fees generated are collected in `fee_collector` module account and then sent to the `distribution` module account in the following block. Then, the `community_tax` and `validator_commission` are subtracted from the collected pool and the resulting amount will be distributed to `Validators` and `Stakers` in accordance with their staked token amount.

> 💡 Note that `Stakers` must claim the rewards manually. Unclaimed rewards will remain in the distribution module account until they are claimed.

Details
-------

```
Staking Rewards = 
   fee pool * (# of delegator's staked tokens / total # of staked tokens) 
   * (1 - community tax rate) * (1 - validator commission rate)
```

The details of how the Staking Rewards are calculated can be found in the [CosmosSDK’s x/distribution documentation](https://docs.cosmos.network/main/build/modules/distribution#the-distribution-scheme).

Parameters
----------

> 💡 The current configuration and parameters can be found by querying the network.

*   `x/distribution: community_tax` : specifies the proportion of fee pool that should be sent to `community_treasury` before staking rewards are distributed. This value can be configured via gov.
*   `x/staking: validator_commission` : specifies the proportion of the staking rewards that a given validator will take from delegator’s reward. This is configured per validator and can be updated by the validator.

See [CosmosSDK doc](https://docs.cosmos.network/main/build/modules/distribution#params) for details.
Title: Trading Rewards

URL Source: https://docs.dydx.xyz/concepts/trading/rewards/trading-rewards

Published Time: Wed, 15 Oct 2025 00:10:49 GMT

Markdown Content:
Trading rewards are designed to incentivize `Traders` to trade on the protocol. The source of trading rewards is a configured `Rewards Treasury` account.

For each successful trade, `Traders` will be rewarded in NATIVE_TOKEN dYdX based on the formula outlined in the below section. Trading rewards are distributed automatically and directly to the trader’s account per block.

Motivation
----------

**The primary goal behind trading rewards is to incentivize trading on the protocol.**
To facilitate fair trading behaviors and to preserve the protocol’s safety, trading rewards have the following secondary goals:

*   Self-trading should not be profitable
*   Any distributed rewards should be proportional to fees paid to the protocol
*   Trading rewards should be deterministic
*   Trading rewards should be settled and distributed every block
*   Trading rewards should limit the protocol overspending on trading activity

Details
-------

![Image 1: Trading Rewards](https://docs.dydx.xyz/trading_rewards.png)

### Reward Treasury

The amount of tokens available to be distributed to traders is tracked by the protocol’s configured Rewards Treasury account. Call the size of this Rewards Treasury `T`.

Each block, new tokens are transferred into this `T` from the vesting account and rewards are then distributed from `T`.

Each block, `T` can grow or shrink based on protocol activity.

### Formula & Emission

We define a trader Total rewards as:

`Total trading rewards = trading reward from taker fee + trading reward from maker fee`

Components of the Trading Rewards formula:

1.   `Taker and Maker Volume`
2.   `Fee Rate`
3.   `Maker Rebates`
4.   `Affiliate Fee Share`
5.   `Protocol Revenue Sharing`
6.   `C Constant`

#### 1. Trading Rewards for Takers

For a taker, rewards in a given block are:

`trading reward from taker fee = taker volume * (taker fee rate - max maker rebate - max possible affiliate taker fee share) * C * (1 - protocol revenue share rate)`

where `max possible affiliate taker fee share` will be:

*   If the taker 30d rolling volume is < = $50M, 50% * taker fee rate regardless of whether the taker is referred or who they are referred by.
*   If the taker 30d rolling volume is > $50M, 0 since the taker doesn’t generate affiliate revenue share.

`Taker Fee Revenue Share` is MegaVault revenue share + Treasury subDAO revenue share + Market Mapper revenue share. You can read more about the revenue share in the governance proposals on Megavault, Treasury subDAO and Market Mapper.

#### 2. Trading Rewards for Makers

Similarly, maker rewards for a user are calculated as:

`trading reward from maker fee = maker volume * (positive maker fees) * C * (1 - protocol revenue share rate)`

### Example

Below is an example using the given formula to calculate the trading reward based on specific inputs for taker volume, fee rates, and other parameters.

In this example, we assume the following values for a trader:

*   `Taker Volume`: totaling $1M in trailing volume in 30 days.
*   `Taker Fee Rate`: taker fee rate of 0.04% assuming they have been referred by a VIP Affiliate, starting at fee tier 3.
*   `Max Maker Rebate`: maximum rebate available for makers is 0.011%.
*   `Max Possible Affiliate Taker Fee Share`: as the trader is referred by a VIP affiliate, entitling the VIP affiliate to 50% of the trader’s taker fee rate.
*   `Taker Fee Revenue Share`: the taker fee revenue share is 60% or 0.6 including 50% to MegaVault and 10% to Treasury subDAO, as well as 0% to market mapper for a given market.
*   `C`: A constant multiplier that is currently set to 0.5 by the dYdX governance, but subject to change through dYdX governance.

```
Trading Reward from Taker Fee = 1,000,000 * (0.0004 − 0.00011 − 0.0002) * 0.4 * (1−0.6)
Trading Reward from Taker Fee = 1,000,000 * 0.00009 * 0.4 * 0.4 = 18
```

For this example, the Trading Reward would be equivalent to $18 in DYDX for an approximate Taker Fee of $400 paid by the user. Note that however since the C factor has been reduced to 0, traders now get rebates directly instead of C constant trading rewards

FAQ
---

> How do trading rewards work from a user perspective?

Traders are rewarded after each successful trade made on the protocol.

Immediately after each fill, a user is sent a certain amount of trading rewards directly to their dYdX Chain address, based on the formulas described below. Prior to each trade, the UI also shows the maximum amount of rewards a trade of that size could receive.

Users earn trading rewards up to, but not exceeding, 90% of a fill’s net-trading-fees, paid in the governance token of the network.

> How do trading rewards affect potential inflation of the governance token?

Trading rewards distributed by the protocol, each block, are capped at the dollar equivalent of the total net trading fees generated by the protocol that block. Thus, trading rewards distributed can fluctuate on a block by block basis.

This can result in a large amount of “savings” by the protocol (via reduced inflation) by not overspending to incentivize trading activity.
Title: dYdX Documentation

URL Source: https://docs.dydx.xyz/concepts/trading/limits/equity-tier-limits

Markdown Content:
Equity Tier Limits
------------------

Subaccounts have a limited number of stateful open orders at any one time determined by the net collateral of the subaccount.

These limits are subject to governance. The latest limits can be queried via the `https://<REST_NODE_ENDPOINT>/dydxprotocol/clob/equity_tier` endpoint.

Here is an example response:

```
"equity_tier_limit_config": {
    "stateful_order_equity_tiers": [
      {
        "usd_tnc_required": "0",
        "limit": 0
      },
      {
        "usd_tnc_required": "20000000",
        "limit": 10
      },
      {
        "usd_tnc_required": "100000000",
        "limit": 20
      },
      {
        "usd_tnc_required": "1000000000",
        "limit": 40
      },
      {
        "usd_tnc_required": "10000000000",
        "limit": 100
      },
      {
        "usd_tnc_required": "50000000000",
        "limit": 200
      }
    ]
}
```

Read as:

| Net Collateral | Long-term / Conditional orders |
| --- | --- |
| < $20 | 0 |
| >= $20 and < $100 | 10 |
| >= $100 and < $1,000 | 20 |
| >= $1,000 and < $10,000 | 40 |
| >= $10,000 and < $100,000 | 100 |
| >= $100,000 | 200 |

For example up to 20 open stateful orders across all markets for a subaccount with a net collateral of $2,000.

Note:

*   Short term orders, including limit `Immediate-or-Cancel`, `Fill-or-Kill`, and market orders on the frontend do not have this limitation.
*   Only the `stateful_order_equity_tiers` field is in effect -- short term order equity limits under the `short_term_order_equity_tiers` key are no longer in effect.
upstream connect error or disconnect/reset before headers. reset reason: connection terminationTitle: Withdrawal Limits

URL Source: https://docs.dydx.xyz/concepts/trading/limits/withdrawal-limits

Markdown Content:
Withdrawal Limits – dYdX Documentation

===============

[Skip to content](https://docs.dydx.xyz/concepts/trading/limits/withdrawal-limits#vocs-content)

[![Image 1: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Guide

API

Concepts

Architecture

Trading

[Limit Orderbook and Matching](https://docs.dydx.xyz/concepts/trading/limit-orderbook)

Markets

Account Operations

Rewards, Fees and Limits

[Rewards and Fees](https://docs.dydx.xyz/concepts/trading/rewards)

Limits

[Equity Tier Limits](https://docs.dydx.xyz/concepts/trading/limits/equity-tier-limits)[Rate Limits](https://docs.dydx.xyz/concepts/trading/limits/rate-limits)[Withdrawal Limits](https://docs.dydx.xyz/concepts/trading/limits/withdrawal-limits)

[Governance Functionalities](https://docs.dydx.xyz/concepts/trading/governance)

[Onboarding FAQs](https://docs.dydx.xyz/concepts/onboarding-faqs)

Nodes

Policies

Search...

[![Image 2: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

[![Image 3: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Menu

Withdrawal Limits

On this page

[Ask in ChatGPT](https://chatgpt.com/?hints=search&q=Please%20research%20and%20analyze%20this%20page%3A%20https%3A%2F%2Fdocs.dydx.xyz%2Fconcepts%2Ftrading%2Flimits%2Fwithdrawal-limits%20so%20I%20can%20ask%20you%20questions%20about%20it.%20Once%20you%20have%20read%20it%2C%20prompt%20me%20with%20any%20questions%20I%20have.%20Do%20not%20post%20content%20from%20the%20page%20in%20your%20response.%20Any%20of%20my%20follow%20up%20questions%20must%20reference%20the%20site%20I%20gave%20you.)

On this page
------------

*   [Withdrawal rate limits](https://docs.dydx.xyz/concepts/trading/limits/withdrawal-limits#withdrawal-rate-limits)
*   [Withdrawal gating](https://docs.dydx.xyz/concepts/trading/limits/withdrawal-limits#withdrawal-gating)

Withdrawal Limits[](https://docs.dydx.xyz/concepts/trading/limits/withdrawal-limits#withdrawal-limits)
======================================================================================================

In an effort to reduce risk across the protocol, withdrawals can be rate limited and gated in specific circumstances.​

Withdrawal rate limits[](https://docs.dydx.xyz/concepts/trading/limits/withdrawal-limits#withdrawal-rate-limits)
----------------------------------------------------------------------------------------------------------------

As a default setting, withdrawals of Noble USDC are rate limited to max(1% of TVL, $1mm) per hour

As a default setting, withdrawals of Noble USDC are rate limited to max(10% of TVL, $10mm) per day

These rate limit parameters can be updated by governance.

Withdrawal gating[](https://docs.dydx.xyz/concepts/trading/limits/withdrawal-limits#withdrawal-gating)
------------------------------------------------------------------------------------------------------

All subaccount transfers and withdrawals will be gated for 50 blocks if a negative collateralized subaccount is seen in state and/or can't be liquidated or deleveraged

All subaccount transfers and withdrawals will also be gated for 50 blocks if a 5+ minute chain outage occurs.

Last updated: 9/19/25, 5:57 AM

[Rate Limits Previous shift←](https://docs.dydx.xyz/concepts/trading/limits/rate-limits)[Governance Functionalities Next shift→](https://docs.dydx.xyz/concepts/trading/governance)
Title: Governance Functionalities

URL Source: https://docs.dydx.xyz/concepts/trading/governance

Published Time: Tue, 21 Oct 2025 21:55:17 GMT

Markdown Content:
Below is a current list of all module parameters that `x/gov` has the ability to update directly. Further documentation will be released which outlines overviews of each custom module, how modules interact with one another, and technical guides regarding how to properly submit governance proposals.

Trading Stats & Fees
--------------------

### Stats Module

The Stats Module tracks user maker and taker volumes over a period of time (aka look-back window). This is currently set to 30 days. The maker and taker volume info is used to place users in corresponding fee-tiers.

Governance has the ability to update the params of the Stats Module, which defines the look-back window (measured in seconds). [Proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/stats/params.proto#L10-L14)

### FeeTiers Module

Governance has the ability to update fee tiers ([proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/feetiers/params.proto#L6-L10)). To read more about fee tiers head to [V4 Deep Dive: Rewards and Parameters](https://dydx.exchange/blog/v4-rewards-and-parameters).

Trading Core
------------

### Insurance Fund

Governance has the ability to send funds from the Protocol’s Insurance Fund. Funds can be sent to individual accounts, or other modules.

Note: any account has the ability to send assets to the Insurance Fund.

### Liquidations Config

Governance has the ability to adjust how liquidations are processed. [Proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/clob/liquidations_config.proto#L8-L34)

*   Max Insurance Fund quantums for deleveraging: The maximum number of quote quantums (exclusive) that the insurance fund can have for deleverages to be enabled.
*   The maximum liquidation fee, in parts-per-million. 100% of this fee goes to the Insurance Fund
*   The maximum amount of how much a single position can be liquidated within one block.
*   The maximum amount of how much a single subaccount can be liquidated within a single block
*   Fillable price config: configuration regarding how the fillable-price spread from the oracle price increases based on the adjusted bankruptcy rating of the subaccount.

### Funding Rate

Governance has the ability to adjust Funding Rate parameters:

*   Funding rate clamp factor, premium vote clamp factor, and min number of votes per premium sample. [Proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/perpetuals/params.proto#L6-L19)
*   Epoch information, which defines the funding interval and premium sampling interval. [Proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/epochs/epoch_info.proto#L6-L43)
*   Liquidity Tier, which defines the impact notional value. [Proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/perpetuals/perpetual.proto#L100-L139)

Trading Rewards
---------------

### Vest Module

The Vest Module is responsible for determining the rate of tokens that vest from Vester Accounts to other accounts such as a Community Treasury Account and a Rewards Treasury Account. The rate of token transfers is linear with respect to time. Thus, block timestamps are used to vest tokens.

Governance has the ability to create, update, or delete a `VestEntry` ([proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/vest/vest_entry.proto#L9-L30)), which defines:

*   The start and end time of vesting
*   The token that is vested
*   The account to vest tokens to
*   The account to vest tokens from

### Rewards Module

The Rewards Module distributes trading rewards to traders (previously written about [V4 Deep Dive: Rewards and Parameters](https://dydx.exchange/blog/v4-rewards-and-parameters)). Governance has the ability to adjust the following ([proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/rewards/params.proto#L6-L26)):

*   Which account Trading Rewards are funded from
*   The token Trading Rewards are funded in
*   The market which tracks the oracle price of the token that Trading Rewards are funded in
*   `C` which is a protocol constant further explained in the post linked above

Markets
-------

### Oracles

Governance has the ability to adjust the list of oracles used for each market. [Proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/prices/market_param.proto#L31-L33)

Note that this functionality does not include creating / removing an exchange-source supported by the protocol as a whole, which will require a binary upgrade.

### Liquidity Tiers

Liquidity Tiers group markets of similar risk into standardized risk parameters. Liquidity tiers specify the margin requirements needed for each market and should be determined based on the depth of the relative market’s spot book as well as the token’s market capitalization.

[Current Liquidity](https://dydx-ops-rest.kingnodes.com/dydxprotocol/perpetuals/liquidity_tiers) Tiers include:

| ID | Name | initial margin fraction | maintenance fraction (what fraction MMF is of IMF) | impact notional | maintenance margin fraction (as is) | impact notional (as is) | Lower Cap (USDC Millions) | Upper Cap (USDC Millions) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Large-Cap | 0.02 | 0.6 | 500 USDC / IM | 0.012 | 25_000 USDC | None | None |
| 1 | Small-Cap | 0.1 | 0.5 | 500 USDC / IM | 0.05 | 5_000 USDC | 20 | 50 |
| 2 | Long-Tail | 0.2 | 0.5 | 500 USDC / IM | 0.1 | 2_500 USDC | 5 | 10 |
| 3 | Safety | 1 | 0.2 | 2500 USDC / IM | 0.2 | 2_500 USDC | 2 | 5 |
| 4 | Isolated | 0.05 | 0.6 | 125 USDC / IM | 0.03 | 2_500 USDC | 0.5 | 1 |
| 5 | Mid-Cap | 0.05 | 0.6 | 250 USDC / IM | 0.03 | 5_000 USDC | 40 | 100 |
| 6 | FX | 0.01 | 0.5 | 25 USDC / IM | 0.0005 | 2_500 USDC | 0.5 | 1 |
| 7 | IML 5x | 0.2 | 0.5 | 25 USDC / IM | 0.1 | 125 USDC | 0.5 | 1 |

*   Each market has a `Lower Cap` and `Upper Cap` denominated in USDC.
*   Each market already has a `Base IMF`.
*   At any point in time, for each market:
    *   Define
        *   `Open Notional = Open Interest * Oracle Price`
        *   `Scaling Factor = (Open Notional - Lower Cap) / (Upper Cap - Lower Cap)`
        *   `IMF Increase = Scaling Factor * (1 - Base IMF)`

    *   Then a market’s `Effective IMF = Min(Base IMF + Max(IMF Increase, 0), 1.0)`

*   The effective IMF is the base IMF while the Open Notional < Lower Cap, and increases linearly until Open Notional = Upper Cap, at which point the IMF stays at 1.0 (requiring 1:1 collateral for trading)

Governance has the ability to create and modify Liquidity Tiers as well as update existing markets’ Liquidity Tier placements. ([proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/perpetuals/perpetual.proto#L100-L139))

### Updating a Live Market

This functionality allows the community to update parameters of a live market, which can be composed of 4 parts

*   Updating a liquidity tier
*   Perpetual (`x/perpetuals`), governance-updatable through `MsgUpdatePerpetualFeeParams` ([proto definition](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/feetiers/tx.proto#L19))
*   Market (`x/prices`), governance-updatable through `MsgUpdateMarketParam` ([proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/prices/market_param.proto#L6-L34))
*   Clob pair (`x/clob`), governance-updatable through `MsgUpdateClobPair` ([proto](https://github.com/dydxprotocol/v4-chain/blob/b2c6062b4e588b98a51454f50da9e8e712cfc2d9/proto/dydxprotocol/clob/tx.proto#L102))

### Adding New Markets

The action of a governance proposal is defined by the [list of messages that are executed](https://github.com/dydxprotocol/cosmos-sdk/blob/4fadfe5a4606b6dc76644d377ed34420f3b80801/x/gov/abci.go#L72-L90) when it’s accepted. A proposal to add a new market should include the following messages (in this particular order):

```
MsgCreateOracle (create objects in x/prices)
MsgCreatePerpetual (create object in x/perpetual)
MsgCreatePerpetualClobPair (create object in x/clob)
MsgDelayMessage (schedule a MsgSetClobPairStatus to enable trading in x/clob)
```

Safety
------

### Spam Mitigation

To prevent spam on the orderbook and prevent the blockchain state from getting too large, governance has the ability to adjust:

*   How many open orders a subaccount can have based on its equity tier. [Proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/clob/equity_tier_limit_config.proto#L8-L19)
*   Order placement rate limits. [Proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/clob/block_rate_limit_config.proto#L8-L35)

Bridge
------

### Bridge Module

The Bridge Module is responsible for receiving bridged tokens from the Ethereum blockchain.

Governance has the ability to update:

*   Event Parameters: Specifies which events to recognize and which tokens to mint. [Proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/bridge/params.proto#L9-L20)
*   Proposal Parameters: Determines how long a validator should wait until it proposes a bridge event to other validators, and how many or often to propose new bridge events. [Proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/bridge/params.proto#L22-L45)
*   Safety Parameters: Determines if bridging is enabled/disabled and how many blocks mints are delayed after being accepted by consensus. [Proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/bridge/params.proto#L47-L55)

Community Assets
----------------

### Community Pool & Treasury

There are two addresses intended for managing funds owned by the community:

1.   a Community Pool and
2.   a Community Treasury.

The Community Pool is the recipient of any Community Tax that is implemented via the Distribution Module. The Community Pool is controllable by governance.

The Community Treasury is an account controlled by governance and can be funded via any account or module sending tokens to it.

CosmosSDK Default Modules
-------------------------

For more information on default modules, head to the [Cosmos SDK official documentation](https://docs.cosmos.network/v0.47/modules). dYdX Chain inherits the same governance properties of any standard CosmosSDK modules that are present on dYdX Chain,
Title: Onboarding FAQs

URL Source: https://docs.dydx.xyz/concepts/onboarding-faqs

Published Time: Fri, 17 Oct 2025 17:17:25 GMT

Markdown Content:
[Skip to content](https://docs.dydx.xyz/concepts/onboarding-faqs/#vocs-content)

[![Image 1: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

[![Image 2: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Background
----------

1. How does the network work? 
*   dYdX Chain (or "v4") is composed of full nodes and each maintains an in-memory order book. Anyone can use the open source software to run a full node. Traders can submit order placements and cancellations to full nodes, which gossip the transactions amongst themselves.
*   Full nodes with enough delegated layer 1 governance tokens participate in block building as validators. Validators on dYdX Chain take turns proposing blocks of trades every ~1 second. The validator whose turn it is to propose a block at a given height is called the proposer. The proposer uses its mempool orderbook to propose a block of matches, which validators either accept or reject according to CometBFT (Tendermint) consensus.
*   All full nodes have visibility into the consensus process and the transactions in the mempool. Another component of dYdX Chain is the indexer software, an application that reads data from full nodes and exposes it via REST / WebSocket APIs for convenience.

2. What is the difference between a full node and a validator?
*   A full node does not participate in consensus. It receives data from other full nodes and validators in the network via the gossip protocol. A validator participates in consensus by broadcasting votes signed by each validator’s private keys.

3. What are the benefits of running a full node as a market maker?
*   Running a full node will eliminate the latency between placing an order and when the actual order is gossiped throughout the network. Without your own node, your order will need to first be relayed to the nearest geographic node, which will then propagate it throughout the network for you. With your own node, your order will directly be gossiped.
*   Additionally, running a full node allows you to use [full node streaming](https://docs.dydx.xyz/nodes/full-node-streaming), a feature that aims to provide real-time, accurate orderbook updates and fills.
*   Instructions on setting up a full node can be found [here](https://docs.dydx.xyz/nodes/running-node/setup).

4. What is the current block time?
*   The current block time is ~1 second on average.

5. What is an indexer?
*   The indexer is a read-only service that consumes real-time data from dYdX Chain to a database for visibility to users. The indexer consumes data from dYdX Chain via a connection to a full node. The full node contains a copy of the blockchain and an in-memory order book. When the full node updates its copy of the blockchain and in-memory order book due to processing transactions, it will also stream these updates to the indexer. The indexer keeps the data in its database synced with the full-node using these updates. This data is made available to users querying through HTTPS REST APIs and streaming via websockets. More info can be found [here](https://docs.dydx.xyz/indexer-client).

Trading
-------

1. How can I understand how finality works on dYdX Chain?
*   When your order fills, a block proposer will propose a block containing the fill (visible to the whole network), and then the block will go through consensus. If the block is valid it will be finalized a couple seconds later (in Cosmos-speak this happens at the “commit” stage of consensus after all validators have voted). At that point, an indexer service will communicate the fill to you.
*   It is recommended to post orders with a “Good-Til-Block” of the current block height, and adjusting prices once per block. If the block is published without a match to your order, you know that it is no longer active and did not fill.

2. What are the different order types in dYdX Chain?
*   There are two order types: Short-Term orders and stateful orders.
    *   Short-Term orders are meant for programmatic, low-latency traders that want to place orders with shorter expirations.
    *   Stateful orders are meant for retail that wants to place orders with longer expirations. These orders exist on chain.

3. How does the orderbook work in dYdX Chain for short-term orders?
*   Each validator runs their own in-memory orderbook (also known as mempool), and the set of orders each validator knows about is what order placement transactions are in their mempool.
*   User places a trade on a decentralized front end (e.g., website) or via the typescript or python client that places orders directly to a full node or validator API.
*   The consensus process picks one validator to be the block proposer. The selected validator will propose their view of the matches in the next proposed block.
*   If the matches are valid (orders cross, subaccounts well-collateralized, etc.) and accepted by ⅔+ of validator stake weight (consensus), then the block is committed and those matches are written to state as valid matches.
*   After the block is committed, the updated onchain (and offchain) data is streamed from full nodes to Indexers. The Indexer then makes this data available via API and websockets back to the front end and/or any other outside services querying for this data.
*   Note: the block proposer’s matches are the canonical matches for the next block assuming their block is accepted by consensus.
    *   Other validators maintain a list of matches and those matches might differ from the block proposer’s matches, but if they’re not the block proposer those matches will not be proposed in the next block.
    *   Similarly, the indexer is not the block proposer so its list of matches might be different from the block proposer’s matches, until the network reaches finality.

4. Why should market makers only use short-term orders?
*   Short-Term orders are placed and can be immediately matched after they’re added to the mempool, while stateful orders can only be placed and matched after they’re added to a block.
    *   Short-Term orders should always have superior time priority to stateful orders.
    *   Stateful orders have worse time priority since they can only be matched after they are included on the block, short-term orders can be matched in the same block.

*   Short-Term orders have less restrictive rate limits than stateful order rate limits. See rate limits later on in this section.
*   Short-Term orders can be replaced, and stateful orders currently don’t support replacement.
*   Short-Term orders can be canceled immediately after they’re placed, while stateful orders can only be canceled after they’ve been included in a block.
*   Short-Term orders can be received by validators in any order, while stateful orders have an ordering requirement and will fail to be placed if they’re received out of order.
    *   This is because stateful orders use a “sequence number”, which is equivalent to a nonce on Ethereum. Short-Term orders don’t use this.

5. How can I place a short-term order?
*   Please use the latest dYdX Chain [typescript client](https://www.npmjs.com/package/@dydxprotocol/v4-client-js) to place orders.
*   Please refer to the [order.proto](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/clob/order.proto) for parameter and field definitions.
*   For more advanced order placements, please refer to one of the [validator clients](https://docs.dydx.xyz/interaction/trading).

6. How can I tell if the block proposer has placed my short-term order?
*   The block proposer has proposed and filled the order in the block.
*   The block proposer has the order in their mempool.

7. How can I tell if my short-term order is canceled?
*   Short-term order placements and cancellations are best-effort, and therefore can't be considered final (actually placed or canceled and unfillable) until expiry.
*   A FOK or IOC order is also unfillable after expiry.
*   The indexer **does not** send a websocket notification when a short-term order expires, which happens when the chain height exceeds the goodTilBlock of the order.
*   The block height is the only reliable way to know if a short-term order is canceled with finality.
*   However, the indexer **does** send a websocket notification when a short-term order cancel is received by the indexer's full node.
*   In most cases, this "best effort" cancel means the order is cancelled. However, some small fraction of these cancels are not successful.
*   See [Limit Order Book and Matching](https://docs.dydx.xyz/concepts/trading/limit-orderbook) for more information.

8. How can I replace an order?
*   Replacing an order reuses the short-term order placement function with the [same order ID](https://github.com/dydxprotocol/v4-chain/blob/4eb219b1b726df9ba17c9939e8bb9296f5e98bb3/proto/dydxprotocol/clob/order.proto#L10) and an equal-to-or-greater good til block.
*   Note: when replacing partially-filled orders, the previous fill amount is counted towards your current order.
    *   Example: Buy 1 BTC order @ $20k is filled for 0.5 BTC. After replacing that order with a Buy 2 BTC order @ $25k, that order can only be filled for a maximum of 1.5 BTC. This is because the previously replaced order was already filled for 0.5 BTC.

9. Are fills computed/updates streamed only when a block is finalized? How about order placements?
*   Fills are computed only when a block is finalized.
*   Short term order place / cancel (including IOC / FOK orders being canceled due to not filling / being on the book or POST-ONLY orders crossing) are streamed when the full node the Indexer deployment is listening to receives the order / cancel and not only when the block is finalized.
    *   This is why the status “BEST_EFFORT_OPENED” or “BEST_EFFORT_CANCELED” since the Indexer only knows that a full-node received the order / cancel, and it’s not guaranteed to be true across the whole network.

*   For the orderbook updates, these are sent when the full-node the Indexer is listening to receives orders / cancels and not just when the block is finalized.
    *   For example, when the full-node receives a short term order it will be approximate how much is filled and how much would go on the orderbook. This is what the Indexer uses to stream orderbook updates. However, there is no guarantee that the orderbook looks the same in other nodes in the network.

*   Note that you can now stream the orderbook directly through your full node for the orderbook. Read more about that [here](https://docs.dydx.xyz/nodes/full-node-streaming).

10. Do orders get matched and removed from the book in between blocks?
*   For removal of short term orders, yes they can be removed in between blocks, however this is on a node-by-node basis and not across the whole network.
    *   E.g. a short-term order could be removed on one node, but still be present on another.
    *   When a short-term order expires (current block height > goodtilBlock), then it is guaranteed to be removed from all nodes.

*   For removal of stateful orders, they can be removed from the book in-between blocks. This is on a node-by-node basis.
    *   If the node removing the stateful orders is the block proposer, these stateful order removals will also be propagated to all other nodes, and be entirely removed from the network.

*   For all orders, regarding matching:
    *   For matching, each node on the network will attempt to match the orders as they are received in-between blocks.
    *   Per block, only 1 node (the block proposer) will propagate the matches it’s done during the block to all other nodes in the network. Validator nodes take turns being the block proposer based on their stake weight.
    *   If a set of validators with ⅔+ of the stake weight of the network see the matches propagated as valid, then those matches are included in the block when finalized.
    *   The only matches that occur on the network are the ones in the block.

11. Do certain order types have priority? Are cancels prioritized?
*   Short term orders when received by a node will be matched against its in-memory orderbook.
    *   Cancels of short-term orders are also processed by a node when received.

*   Stateful orders (long-term / conditional) are matched at the end of the block when they are received.
    *   E.g. Stateful orders have at least a 1 block-time delay (it’s possible the order does not get included in the block) between a node receiving the order, and it being matched.
    *   Stateful order placement will be processed AFTER short-term order placements and cancellations for a block.

*   Stateful order cancellations are also done at the end of the block they are received.
    *   The stateful order cancellations are also processed AFTER short-term placements and cancellations for a block.

*   As mentioned above, only the matches from the block proposer will be included in the block (if a set of validators with ⅔+ of the stake weight of the network see the matches as valid).

12. How does the order cancellation mechanism work? 
*   Short-term:
    *   When validators receive a cancellation, if they don't already see a match for the order, they will remove the order from their order book.
    *   Only once every validator receives the cancellation is when the order will no longer be able to be matched.
    *   The other way an order would no longer be matchable is if the block height is past the good til block.

*   Long-term:
    *   Once a stateful order cancellation is included into a block, the order will be canceled and no longer matchable. This could take 1s+ for a cancelation to be included in a block.

13. Why is it slower to cancel orders than place orders?
*   An order placement only needs to be on a single validator to have a match happen, but the cancellation has to have arrived at the block proposer. Since the BP rotates, to be completely sure that the order won't be matched, it has to arrive at all the validators who will be block proposer before the order expires. This is why cancelations seem to be guaranteed slower than placing/matching orders.

14. How do order statuses transition for the Indexer, for short-term and long-term orders?
*   Short-term:
    *   Once the order is placed and seen by the Indexer's full-node, the order has status BEST_EFFORT_OPENED.
    *   If the order is matched and has a fill in a block, the order has status OPEN.
    *   If the order is fully-filled, the order has status FILLED.
    *   If the order is canceled by a cancel order message, the order will have status BEST_EFFORT_CANCELED. The order may still have fills if other validator nodes haven't received the cancel message yet.
    *   If the order expires due to the block height exceeding the good til block of the order, the order status will be CANCELED. The order can no longer be filled.

*   Long-term:
    *   Once the order is placed and included in a block, the order has status OPEN.
    *   If the order is fully filled, the order has status FILLED.
    *   If the cancelation of the order is included in a block, the order has status CANCELED. The order can no longer be filled.

15. How do subaccounts work on dYdX Chain?
*   Each address’s subaccounts all fall under a single address, but they are labeled subaccount0, subaccount1, etc. This is unlike v3, where each subaccount was a secondary address.
*   To begin trading, you need to make sure your funds are in your subaccount. You can do this two ways:
    *   Frontend: Simply leave your frontend open and it will automatically sweep.
    *   Backend: Simply transfer USDC to it like in [this example](https://github.com/dydxprotocol/v4-clients/blob/123cd819939fe47ff80dda04b1ac1144dffa4fda/v4-client-js/examples/transfer_example_subaccount_transfer.ts).

16. Do I need gas when I transfer funds to create a new subaccount?
*   Yes, you will need gas. Fortunately, both USDC and cosmos native dYdX can be used to pay for gas fees. This USDC must be in the main wallet and not another subaccount to pay for fees.
*   To ensure this, the frontend leaves a small amount of USDC in your wallet when sweeping into your subaccount, to ensure there's enough to pay for gas.

17. What impact do subaccounts have on rate limits?
*   Rate limits are per account, and not per subaccount.

18. How do we compete for liquidation orders?
*   If you run a full-node, there is a liquidations daemon that has metrics on what accounts are up for liquidation orders, and they could try and compete for liquidations that way.
*   However, this is not at all documented so you'll have to work it out by reading code.

Full Nodes & Validators
-----------------------

1. How much throughput and latency can be expected from a self-hosted full node? Would having multiple full nodes in different regions improve speed?
*   Throughput of up to 1500 orders/second from our load-testing. Latency depends on which validator is the proposer. Having multiple full-nodes in different regions where there are validators (so maybe 1 in Europe + 1 in Tokyo) would lead to improved latency.

2. Do validators communicate through a public P2P network, or is there an internal network?
*   It's a public P2P network.

3. What is the expected order-to-trade latency under normal conditions?
*   Expected order → trade latency would be:
    *   Time for order to get from the node it was submitted to, to the proposer, so location dependent.
    *   Order match -> trade, probably at least 1 block so ~0.8s, could be more than 1 block.

4. Is it faster to submit transactions directly to a validator or to broadcast transactions to the network? 
*   It is faster to submit a transaction directly to the block proposer. The speed difference between a full-node and a validator is negligible unless that validator is the proposer.

5. Do you have some validators that we can send orders to?
*   Validators don't expose the RPC endpoints for orders.

6. How do other teams improve their speed?
*   Some teams are trying to get data about the order book/order updates from a full-node they are running to improve the latency to receiving data, as there is additional latency to getting order updates due to the Indexer systems having additional latency. We currently do not have documentation around this, but are working on it.

Indexer
-------

1. How does the indexer reconstruct the orderbook when it started/initial snapshot of the book?
*   A full node is run alongside the Indexer and sends messages to the indexer when it receives orders either from the RPC or gossiped from other nodes, as well as any updates from:
    *   node pruning the order when it expires.
    *   another order that matches an order that the node received earlier.
    *   node removing order due to receiving a cancel from RPC or gossip.

*   The indexer also updates the order book whenever it receives these order messages.

2. How does the indexer know what orders are in the book on start up?
*   On a cold-start, a full-node would still have all the stateful orders and would send them to the indexer. For short-term orders, the full-node would not know them, nor would the indexer. Since short-term orders only are valid for 20 blocks, within 20 blocks the indexer would have an accurate view of the order book, but for the first 20 blocks it would not.

MEV
---

1. How will dYdX Chain handle MEV?
*   Unlike general-purpose smart contract environments, the Cosmos infrastructure enables unique MEV solutions to be built that align a validator’s incentives with a user’s incentives. dYdX Chain has a framework where MEV is measured via a [dashboard](https://observatory.zone/dydx/mev). The first step would be to punish validators with slashing. Further proposed solutions are still being considered, and will be announced once finalized.

2. When do I have finality related to fills?
*   When your order fills, a block proposer proposes a block containing the fill (visible to the whole network), and then the block undergoes consensus. If the block is valid, it finalizes shortly thereafter (in Cosmos-speak this happens at the “commit” stage of consensus, after all validators have voted). In Cosmos, every block is final (no reorgs or forks).
*   If you’re connected via full node, you’ll see each step of this process. If you’re connected via the indexer service, you’ll see order updates over webSocket as soon as each block is confirmed.

3. Is deliberately taking canceled orders considered an attack against makers? 
*   Nodes should respect cancels as soon as they receive them. If they don't, then we see that as MEV and the aforementioned dashboard/metrics tracking MEV will track that.

Pricing
-------

1. How is the oracle price computed?
*   The oracle price has five parts:
    *   Skip Protocol Sidecar: side car that pulls price data from external sources and caches them for the validator to use [link](https://docs.skip.build/connect/validators/quickstart).
    *   Vote Extensions: Every block during the Precommit stage, all validators will submit vote extensions for what they believe the oracle price of all tracked assets should be.
    *   Consensus: The block after VE are submitted, Slinky deterministically aggregates all VE from the previous block and proposes a new updated price which is voted into consensus.
    *   `x/prices` Module: updates the state based on the new price, also has logic for validation and etc. [link](https://github.com/dydxprotocol/v4-chain/tree/main/protocol/x/prices).
    *   Params: determines the external sources and sensitivity [link](https://github.com/dydxprotocol/v4-testnets/blob/aa1c7ac589d6699124942a66c2362acad2e6f50d/dydx-testnet-4/genesis.json#L6106), these are configured per network (testnet genesis example), but should query the network config for these `dydxprotocold query prices list-market-param`.

Rewards
-------

1. How will trading rewards work on dYdX Chain?
*   Trading rewards are not controlled by dYdX. dYdX recommends that trading rewards could be calculated primarily based on total taker fees paid, along with a few other variables. The full proposed formula can be found [here](https://docs.dydx.xyz/concepts/trading/rewards),

2. Do liquidity provider rewards exist on v4 (dYdX Chain)?
*   Liquidity provider rewards in v4 are not controlled by dYdX. dYdX recommends that liquidity provider rewards should cease to exist in v4. Makers could be rewarded with a maker rebate ranging from 0.5bps to 1.1bps, based on their nominal volume and volume share. The full proposed fee schedule can be found [here](https://docs.dydx.xyz/concepts/trading/rewards).
