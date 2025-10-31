Title: Quick Start with Python

URL Source: https://docs.dydx.xyz/interaction/client/quick-start-py

Published Time: Tue, 14 Oct 2025 09:43:58 GMT

Markdown Content:
Quick Start with Python – dYdX Documentation

===============

[Skip to content](https://docs.dydx.xyz/interaction/client/quick-start-py#vocs-content)

[![Image 1: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Guide

Getting Started

[Quick start with Python](https://docs.dydx.xyz/interaction/client/quick-start-py)[Quick start with Rust](https://docs.dydx.xyz/interaction/client/quick-start-rs)[Quick start with TypeScript](https://docs.dydx.xyz/interaction/client/quick-start-ts)

[Preparing to Trade](https://docs.dydx.xyz/interaction/endpoints)[Wallet Setup](https://docs.dydx.xyz/interaction/wallet-setup)[Trading](https://docs.dydx.xyz/interaction/trading)

Trading Data

[Permissioned Keys](https://docs.dydx.xyz/interaction/permissioned-keys)

Deposits & Withdrawals

Application Integration

API

Concepts

Nodes

Policies

Search...

[![Image 2: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

[![Image 3: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Menu

Quick start with Python

On this page

[Ask in ChatGPT](https://chatgpt.com/?hints=search&q=Please%20research%20and%20analyze%20this%20page%3A%20https%3A%2F%2Fdocs.dydx.xyz%2Finteraction%2Fclient%2Fquick-start-py%20so%20I%20can%20ask%20you%20questions%20about%20it.%20Once%20you%20have%20read%20it%2C%20prompt%20me%20with%20any%20questions%20I%20have.%20Do%20not%20post%20content%20from%20the%20page%20in%20your%20response.%20Any%20of%20my%20follow%20up%20questions%20must%20reference%20the%20site%20I%20gave%20you.)

On this page
------------

*   [Install Python3 and Poetry](https://docs.dydx.xyz/interaction/client/quick-start-py#install-python3-and-poetry)
*   [Clone the dydx client repo](https://docs.dydx.xyz/interaction/client/quick-start-py#clone-the-dydx-client-repo)
*   [Install all dependencies](https://docs.dydx.xyz/interaction/client/quick-start-py#install-all-dependencies)
*   [Run an example](https://docs.dydx.xyz/interaction/client/quick-start-py#run-an-example)

Quick Start with Python[](https://docs.dydx.xyz/interaction/client/quick-start-py#quick-start-with-python)
==========================================================================================================

This guide will walk you through the steps to set up and start using the dYdX API Python library.

Install Python3 and Poetry[](https://docs.dydx.xyz/interaction/client/quick-start-py#install-python3-and-poetry)
----------------------------------------------------------------------------------------------------------------

Choose and install [Python 3.9+](https://www.python.org/downloads/) and [Poetry](https://python-poetry.org/docs#installing-with-the-official-installer) for your system.

Clone the dydx client repo[](https://docs.dydx.xyz/interaction/client/quick-start-py#clone-the-dydx-client-repo)
----------------------------------------------------------------------------------------------------------------

`git clone https://github.com/dydxprotocol/v4-clients.git`

Install all dependencies[](https://docs.dydx.xyz/interaction/client/quick-start-py#install-all-dependencies)
------------------------------------------------------------------------------------------------------------

Go to the Python client library.

`cd v4-clients/v4-client-py-v2`

Install the project dependencies using the following command:

`poetry install`

Run an example[](https://docs.dydx.xyz/interaction/client/quick-start-py#run-an-example)
----------------------------------------------------------------------------------------

Now, we can run an example file. Let's run `example/accounts_endpoint.py` file.

`poetry run python -m examples.account_endpoints`

**Now, you can play around with all the available examples. Happy trading!**

**Python Package**
The Python client is also available through the PyPI [package](https://pypi.org/project/dydx-v4-client/)`dydx-v4-client`.

Installation

`pip install dydx-v4-client`

Last updated: 9/19/25, 5:57 AM

[Quick start with Rust Next shift→](https://docs.dydx.xyz/interaction/client/quick-start-rs)
Title: Connecting to dYdX

URL Source: https://docs.dydx.xyz/interaction/endpoints

Published Time: Tue, 14 Oct 2025 09:43:59 GMT

Markdown Content:
dYdX provides two networks for trading: a **mainnet**, and a **testnet**:

*   **mainnet**: The core network where real financial transactions occur;
*   **testnet**: A separate, risk-free, network. Served mainly for the purposes of testing and experimenting before transitioning to the **mainnet**.

For the purposes of this guide, we'll assume that the **mainnet** is being used. Nevertheless, the API is exactly the same for both the **mainnet** and the **testnet**, so any code working in the **mainnet** should work in the **testnet**. Choosing between the **mainnet** and the **testnet** is simply a matter of changing the used endpoints.

Available clients
-----------------

Interacting with the dYdX network API is made through several sets of methods grouped with structures referred to as clients. Each of these clients essentially connects to a different server with its own functionality and purpose.

### Node client

The Node client (also known as the Validator client) is the main client for interacting with the dYdX network. It provides the [Node API](https://docs.dydx.xyz/node-client) allowing the user to do operations that require authentication (e.g., issue trading orders) through the [Private API](https://docs.dydx.xyz/node-client/private).

You'll need an endpoint to setup the Node client. Grab an RPC/gRPC endpoint from [here](https://docs.dydx.xyz/interaction/endpoints#node). Additionally for the Python client, you'all also need a HTTP and WebSockets endpoints.

Python

```
from dydx_v4_client.network import make_mainnet
from dydx_v4_client.node.client import NodeClient
 
config = make_mainnet( 
   node_url="oegs.dydx.trade:443"
   rest_indexer="https://indexer.dydx.trade", 
   websocket_indexer="wss://indexer.dydx.trade/v4/ws", 
).node 
# Call make_testnet() to use the testnet instead. 
 
# Connect to the network. 
node = await NodeClient.connect(config)
```

While the Node client can also query data through the [Public API](https://docs.dydx.xyz/node-client/public), the Indexer client should be preferred.

### Indexer client

The Indexer is a high-availability system designed to provide structured data and offload computational burden from the core full nodes. The Indexer client provides methods from the [Indexer API](https://docs.dydx.xyz/indexer-client). It serves both as a spontaneuous source of data retrieval through its REST endpoint, or a continuous feed of trading data through its WebSockets endpoint.

Given that the Indexer client can use these two different protocols, you'll need two endpoints to setup it up. Grab these from [here](https://docs.dydx.xyz/interaction/endpoints#indexer).

Python

```
from dydx_v4_client.network import make_mainnet
from dydx_v4_client.indexer.rest.indexer_client import IndexerClient
from dydx_v4_client.indexer.socket.websocket import IndexerSocket
 
config = make_mainnet( 
   node_url="your-custom-grpc-node.com", 
   rest_indexer="https://your-custom-rest-indexer.com", 
   websocket_indexer="wss://your-custom-websocket-indexer.com"
).node 
 
# Instantiate the HTTP sub-client. 
indexer = IndexerClient(config.rest_indexer) 
# Instatiate the WebSockets sub-client, connecting to the network. 
socket = await IndexerSocket(network.websocket_indexer).connect()
```

### Composite client (TypeScript only)

The Composite client groups commonly used methods into a single structure. It is essentially composed by both the Node and Indexer clients.

TypeScript

```
import { CompositeClient, Network } from '@dydxprotocol/v4-client-js';
 
const network = Network.mainnet();
const client = await CompositeClient.connect(network);
```

### Faucet client

To test your trading strategy, test funds can be requested from the Faucet client. This client only works in the **testnet**. The acquired test funds can only be used in the **testnet**.

Python

```
from dydx_v4_client.network import TESTNET_FAUCET
from dydx_v4_client.faucet_client import FaucetClient
 
faucet = FaucetClient(TESTNET_FAUCET)
```

### Noble client

To move assets in and out of the dYdX network, the Noble network is commonly employed.

Python

```
from dydx_v4_client.indexer.rest.noble_client import NobleClient
 
client = NobleClient("https://rpc.testnet.noble.strange.love") 
await client.connect(MNEMONIC)
```

Endpoints
---------

Some known endpoints are provided below. Use these to connect to the dYdX networks. Feel free to compare the most suitable gRPC endpoint from this [status endpoint](https://grpc-status.dydx.trade/)

### Node

Connections with the full nodes are established using the (g)RPC protocol.

#### mainnet

##### gRPC

| Team | URI | Rate limit |
| --- | --- | --- |
| OEGS | `grpc://oegs.dydx.trade:443` |  |
| Polkachu | `https://dydx-dao-grpc-1.polkachu.com:443` `https://dydx-dao-grpc-2.polkachu.com:443` `https://dydx-dao-grpc-3.polkachu.com:443` `https://dydx-dao-grpc-4.polkachu.com:443` `https://dydx-dao-grpc-5.polkachu.com:443` | 300 req/m |
| KingNodes | `https://dydx-ops-grpc.kingnodes.com:443` | 250 req/m |
| Enigma | `https://dydx-dao-grpc.enigma-validator.com:443` |  |
| Lavender.Five | `https://dydx.lavendarfive.com:443` |  |
| PublicNode | `https://dydx-grpc.publicnode.com:443` |  |

##### RPC

| Team | URI | Rate limit |
| --- | --- | --- |
| OEGS | `https://oegs.dydx.trade:443` |  |
| Polkachu | `https://dydx-dao-rpc.polkachu.com:443` | 300 req/m |
| KingNodes | `https://dydx-ops-rpc.kingnodes.com:443` | 250 req/m |
| Enigma | `https://dydx-dao-rpc.enigma-validator.com:443` |  |
| Lavender.Five | `https://dydx-rpc.lavenderfive.com:443` |  |
| AutoStake | `https://dydx-mainnet-rpc.autostake.com:443` | 4 req/s |
| EcoStake | `https://rpc-dydx.ecostake.com:443` |  |
| PublicNode | `https://dydx-rpc.publicnode.com:443` |  |

##### REST

| Team | URI | Rate limit |
| --- | --- | --- |
| Polkachu | `https://dydx-dao-api.polkachu.com:443` | 300 req/m |
| KingNodes | `https://dydx-ops-rest.kingnodes.com:443` | 250 req/m |
| Enigma | `https://dydx-dao-lcd.enigma-validator.com:443` |  |
| Lavender.Five | `https://dydx-api.lavenderfive.com:443` |  |
| AutoStake | `https://dydx-mainnet-lcd.autostake.com:443` | 4 req/s |
| EcoStake | `https://rest-dydx.ecostake.com:443` |  |
| PublicNode | `https://dydx-rest.publicnode.com:443` |  |

#### testnet

##### gRPC

| Team | URI |
| --- | --- |
| OEGS | `oegs-testnet.dydx.exchange:443` |
| Lavender Five | `testnet-dydx.lavenderfive.com:443 (TLS)` |
| King Nodes | `test-dydx-grpc.kingnodes.com:443 (TLS)` |
| Polkachu | `dydx-testnet-grpc.polkachu.com:23890 (plaintext)` |

##### RPC

| Team | URI |
| --- | --- |
| OEGS | `https://oegs-testnet.dydx.exchange:443` |
| Enigma | `https://dydx-rpc-testnet.enigma-validator.com` |
| Lavender Five | `https://testnet-dydx-rpc.lavenderfive.com` |
| King Nodes | `https://test-dydx-rpc.kingnodes.com` |
| Polkachu | `https://dydx-testnet-rpc.polkachu.com` |

##### REST

| Team | URI |
| --- | --- |
| Enigma | `https://dydx-lcd-testnet.enigma-validator.com` |
| Lavender Five | `https://testnet-dydx-api.lavenderfive.com` |
| King Nodes | `https://test-dydx-rest.kingnodes.com` |
| Polkachu | `https://dydx-testnet-api.polkachu.com` |

### Indexer

Connections with the Indexer are established either using HTTP (for spontaneuous data retrieval) or WebSockets (for data streaming).

#### mainnet

| Type | URI |
| --- | --- |
| HTTP | `https://indexer.dydx.trade/v4` |
| WS | `wss://indexer.dydx.trade/v4/ws` |

#### testnet

| Type | URI |
| --- | --- |
| HTTP | `https://indexer.v4testnet.dydx.exchange` |
| WS | `wss://indexer.v4testnet.dydx.exchange/v4/ws` |

### Faucet

Used to retrieve test funds.

#### testnet

`https://faucet.v4testnet.dydx.exchange`

### Noble

Connections with the Noble blockchain. Similarly to the dYdX networks, Noble also has a **mainnet** and a **testnet**.

#### mainnet

| Team | URI |
| --- | --- |
| Polkachu | `http://noble-grpc.polkachu.com:21590 (plaintext)` |

#### testnet

| Team | URI |
| --- | --- |
| Polkachu | `noble-testnet-grpc.polkachu.com:21590 (plaintext)` |
Title: Wallet Setup

URL Source: https://docs.dydx.xyz/interaction/wallet-setup

Published Time: Tue, 21 Oct 2025 21:35:05 GMT

Markdown Content:
To manage your accounts, issue orders, and perform other operations that are required to be signed, a Wallet is required. To instantiate a Wallet, you must first have your associated **mnemonic**.

Unification Plan
*   The Python client requires the use of an address to setup the Wallet. However, the address can only be fetched using a Wallet. The address is derived from the mnemonic (address < public key < private key < mnemonic).
*   Wallet, accounts, subaccounts are all handled differently among the clients. Probably the Rust client handles this best, giving the user more control:
    1.   There is a `Wallet`;
    2.   The `Wallet` is used to derive an `Account` by index (each `Account` is associated with a keypair);
    3.   An `Account` is used to derive a `Subaccount` by index. A `Subaccount` is employed to create orders.

Getting the mnemonic
--------------------

A Wallet is setup using your secret **mnemonic** phrase. A **mnemonic** is a set of 24 words to back up and access your account.

You can fetch your **mnemonic** from the [dYdX Frontend](https://dydx.trade/). After logging in, follow the instructions in "Export secret phrase", accessed by clicking your address in the upper right corner.

For the purpose of this guide, lets copy and store the **mnemonic** in a `mnemonic.txt` file.

Read the mnemonic
-----------------

Lets start coding. Load the mnemonic into a string variable. This assumes the mnemonic is stored in a text file.

Python

`mnemonic = open('mnemonic.txt').read().strip()`

Create the Wallet
-----------------

Use the **mnemonic** to create a Wallet instance capable of signing transactions.

Python

```
from dydx_v4_client.key_pair import KeyPair
from dydx_v4_client.wallet import Wallet
 
# Define your address.
address = Wallet(KeyPair.from_mnemonic(mnemonic), 0, 0).address()
 
# Create a Wallet with updated parameters required for trading
wallet = await Wallet.from_mnemonic(node, mnemonic, address)
```

Instantiate a Subaccount
------------------------

When issuing orders, the relevant Subaccount must be chosen to place the order under. A Subaccount is associated with an Account, and is meant to provide trade isolation against your other Subaccounts and enhance funds management. See more about [Accounts and Subaccounts](https://docs.dydx.xyz/concepts/trading/accounts).

Python

```
# Not required. The `wallet` instance created above already contains the necessary information.
# The Subaccount to be used is defined using an integer when creating an order.
```
Title: Trading

URL Source: https://docs.dydx.xyz/interaction/trading

Markdown Content:
Interacting with the dYdX perpetual markets and managing your positions is done by placing orders. Enter `LONG` positions by placing buy orders and `SHORT` positions by placing sell orders.

Place an order
--------------

To place an [order](https://docs.dydx.xyz/concepts/trading/orders), you'll need your wallet ready to sign transactions. Please check the [Wallet Setup](https://docs.dydx.xyz/interaction/wallet-setup) guide to check how to set up a wallet. In this guide we'll be creating a short-term buy order for the ETH-USD market.

### Get market parameters

To create an order for a specific market (identified by its ticker, or _CLOB pair ID_), we should first fetch the market parameters that allows us to do data conversions associated with that specific market. Other parameters such as the current price can also be fetched this way.

Python

```
MARKET_ID = 1 # ETH-USD identifier
# Fetch market parameters.
market = Market(
    (await indexer.markets.get_perpetual_markets(MARKET_ID))["markets"][MARKET_ID]
)
# Current price.
print(market["oraclePrice"])
```

### Creating an order

#### Identifying the order

Every order created has an unique identifier, referred to as the **order ID**. It can be calculated locally and is composed of,

*   **Subaccount ID**: The account address plus the integer identifying the subaccount;
*   **Client ID**: A 32-bit integer chosen by the user to identify the order. Two orders can't have the same client ID;
*   **Order flags**: An integer identifying if the order is short-term (`0`), long-term (`64`), or conditional (`32`);
*   **CLOB Pair ID**: The ID of the underlying market/perpetual.

Python

```
order_id = market.order_id(
    ADDRESS, # address
    0, # subaccount number
    random.randint(0, 100000000), # chosen client ID, can be random
    OrderFlags.SHORT_TERM # short-term order
)
```

#### Building the order

In dYdX, orders can be either short-term or long-term, see a comparison [here](https://docs.dydx.xyz/concepts/trading/orders). A wide range of order types and parameters are provided to allow for different types of trading strategies.

*   [**Type**](https://docs.dydx.xyz/types/order_type): Market, Limit, and Stop, and Take Profit orders are supported;
*   [**Side**](https://docs.dydx.xyz/types/order_side): Purchase (`BUY`) or sell (`SELL`);
*   **Size**: A decimal value corresponding to the quantity being traded;
*   **Price**: A decimal value corresponding to the chosen price;
*   [**Time in Force**](https://docs.dydx.xyz/types/time_in_force): Execution option, defining conditions for order placements;
*   **Reduce Only**: A boolean value, used to label orders that can only reduce your position size. For example, a 1.25 BTC Sell Reduce Only order on a 1 BTC long:
    *   If **true**: can only decrease your position size by 1. The remaining .25 BTC sell will not fill and be cancelled;
    *   Else: The remaining .25 BTC sell can fill and the position become .25 BTC short.

*   **Good until Block**: Validity of the order. It is an integer value, different for short-term and long-term orders:
    *   **Short-term**: Short term orders have a maximum validity of current block height + `ShortBlockWindow`. Currently, `ShortBlockWindow` is 20 blocks, or about 30 seconds;
    *   **Long-term**: Stateful orders have a maximum validity of current block time + `StatefulOrderTimeWindow`. Currently, `StatefulOrderTimeWindow` this value is 95 days.

Python

```
# Order valid for the next 10 blocks.
good_til_block = await node.latest_block_height() + 10
# Create the order.
order = market.order(
    order_id,
    OrderType.LIMIT,
    Order.Side.SIDE_BUY,
    size=0.01, # ETH
    price=1000, # USDC
    time_in_force=Order.TimeInForce.TIME_IN_FORCE_UNSPECIFIED,
    reduce_only=False,
    good_til_block=good_til_block, # valid until this (future) block
)
```

### Broadcasting an order

With the order now built, we can push it to the dYdX network.

Python

```
# Broadcast the order.
place = await node.place_order(wallet, order)
```

Cancel an order
---------------

An unfilled order can be cancelled. The **order ID** is required to cancel an order.

Python

```
cancel_tx = await node.cancel_order(
    wallet, order_id, good_til_block
)
```
