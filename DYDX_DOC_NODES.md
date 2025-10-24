Title: Hardware Requirements

URL Source: https://docs.dydx.xyz/nodes/running-node/hardware-requirement

Published Time: Tue, 21 Oct 2025 21:56:48 GMT

Markdown Content:
Hardware Requirements – dYdX Documentation

===============

[Skip to content](https://docs.dydx.xyz/nodes/running-node/hardware-requirement#vocs-content)

[![Image 3: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Guide

API

Concepts

Nodes

Running Your Node

[Hardware Requirements](https://docs.dydx.xyz/nodes/running-node/hardware-requirement)[Required Node Configs](https://docs.dydx.xyz/nodes/running-node/required-node-configs)[Setup](https://docs.dydx.xyz/nodes/running-node/setup)[Optimize](https://docs.dydx.xyz/nodes/running-node/optimize)[Running a Validator](https://docs.dydx.xyz/nodes/running-node/running-a-validator)[Snapshots](https://docs.dydx.xyz/nodes/running-node/snapshots)[Peering with Gateway](https://docs.dydx.xyz/nodes/running-node/peering-with-gateway)[Voting](https://docs.dydx.xyz/nodes/running-node/voting)

[Node Streaming](https://docs.dydx.xyz/nodes/full-node-streaming)

Upgrades

[Network Constants](https://docs.dydx.xyz/nodes/network-constants)[Resources](https://docs.dydx.xyz/nodes/resources)

Policies

Search...

[![Image 4: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

[![Image 5: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Menu

Hardware Requirements

On this page

[Ask in ChatGPT](https://chatgpt.com/?hints=search&q=Please%20research%20and%20analyze%20this%20page%3A%20https%3A%2F%2Fdocs.dydx.xyz%2Fnodes%2Frunning-node%2Fhardware-requirement%20so%20I%20can%20ask%20you%20questions%20about%20it.%20Once%20you%20have%20read%20it%2C%20prompt%20me%20with%20any%20questions%20I%20have.%20Do%20not%20post%20content%20from%20the%20page%20in%20your%20response.%20Any%20of%20my%20follow%20up%20questions%20must%20reference%20the%20site%20I%20gave%20you.)

On this page
------------

*   [Minimum Specs](https://docs.dydx.xyz/nodes/running-node/hardware-requirement#minimum-specs)

Hardware Requirements[](https://docs.dydx.xyz/nodes/running-node/hardware-requirement#hardware-requirements)
============================================================================================================

Minimum Specs[](https://docs.dydx.xyz/nodes/running-node/hardware-requirement#minimum-specs)
--------------------------------------------------------------------------------------------

The minimum recommended specs for running a node is the following:

*   16-core, x86_64 architecture processor
*   64 GiB RAM
*   500 GiB of locally attached SSD storage

For example, an AWS instance like the `r6id.4xlarge`, or equivalent.

Last updated: 9/19/25, 5:57 AM

[Onboarding FAQs Previous shift←](https://docs.dydx.xyz/concepts/onboarding-faqs)[Required Node Configs Next shift→](https://docs.dydx.xyz/nodes/running-node/required-node-configs)
Title: Required Node Configs

URL Source: https://docs.dydx.xyz/nodes/running-node/required-node-configs

Published Time: Tue, 14 Oct 2025 09:51:38 GMT

Markdown Content:
These configurations must be applied for both full nodes and validators.

💡Note: failure to set up below configurations on a validator node may compromise chain functionality.

The dYdX Chain has important node configurations required for normal chain operation. This includes:

*   The `config.toml` file read by CometBFT
    *   ([Full documentation](https://docs.cometbft.com/v0.38/core/configuration))

*   The `app.toml` file read by CosmosSDK
    *   ([Full documentation](https://docs.cosmos.network/main/learn/advanced/config))

### `config.toml`

#### Consensus Configs

```
[consensus]
timeout_commit = "500ms"
```

### `app.toml`

#### Base Configuration

Replace `$NATIVE_TOKEN_DENOM` at the end of the field with the correct value from [Network Constants](https://docs.dydx.xyz/nodes/network-constants)

```
### Gas Prices ###
minimum-gas-prices = "0.025ibc/8E27BA2D5493AF5636760E354E46004562C46AB7EC0CC4C1CA14E9E20E2545B5,12500000000$NATIVE_TOKEN_DENOM"
```

```
### Pruning ###
pruning = "custom"
 
# Small numbers >= "2" for validator nodes.
# Larger numbers could be used for full-nodes if they are used for historical queries.
pruning-keep-recent = "7"
 
# Any prime number between "13" and "97", inclusive.
pruning-interval = "17"
```

#### gRPC Configs

```
[grpc]
# Enable grpc. The Cosmos gRPC service is used by various daemon processes,
# and must be enabled in order for the protocol to operate:
enable = true
 
# Non-standard gRPC ports are not supported at this time. Please run on port 9090, which is the default
# port specified in the config file.
# Note: grpc can be also be configured via start flags. Be careful not to change the default settings
# with either of the following flags: `--grpc.enable`, `--grpc.address`.
address = "0.0.0.0:9090"
```
Title: Set Up a Full Node

URL Source: https://docs.dydx.xyz/nodes/running-node/setup

Markdown Content:
Installing and running a full node allows you to read orderbook and onchain data from a network, as well as place, confirm and cancel orders directly on that network.

For example, an AWS instance like the `r6id.4xlarge`, or equivalent.

Save the script with an `.sh` extension in your `$HOME` directory. Edit the script, replacing default values in fields such `VERSION` and `CHAIN-ID` with your own. Run the script with the following commands:

The following steps will guide you through manually setting up a full node.

Run the commands in this procedure from your home directory unless otherwise specified. To change directories to your home folder, run the following command:

### Update your system and prepare to install dependencies

To download system updates and install [curl](https://curl.se/), [jq](https://jqlang.github.io/jq/), and [lz4](https://lz4.org/), run the following commands:

```
sudo apt-get -y update
sudo apt-get install -y curl jq lz4
```

### Install Go

To install [Go](https://go.dev/), run the following commands using the latest version of Go:

```
# Example for AMD64 architecture and Go version 1.22.2
wget https://golang.org/dl/go1.22.2.linux-amd64.tar.gz # Download the compressed file
sudo tar -C /usr/local -xzf go1.22.2.linux-amd64.tar.gz # Extract the file to /usr/local
rm go1.22.2.linux-amd64.tar.gz # Delete the installer package
```

Add the Go directory to your system `$PATH`:

`echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> $HOME/.bashrc # Write to your .bashrc profile`

### Install Cosmovisor and create data directories

[Cosmovisor](https://docs.cosmos.network/main/build/tooling/cosmovisor) is a process manager for Cosmos SDK-based blockchains that enables automatic binary updates without downtime. To install the latest version of Cosmovisor, run the following command:

`go install cosmossdk.io/tools/cosmovisor/cmd/cosmovisor@latest`

To create data directories for Cosmovisor, run the following commands:

```
mkdir -p $HOME/.dydxprotocol/cosmovisor/genesis/bin
mkdir -p $HOME/.dydxprotocol/cosmovisor/upgrades
```

### Download the `dydxprotocold` binary

The `dydxprotocold` binary contains the software you need to operate a full node. **You must use the same version of the software as the network to which you want to connect.** To find the current version of the [dYdX Foundation](https://www.dydx.foundation/) mainnet, see the recommended protocol version on [mintscan.io](https://www.mintscan.io/dydx/parameters).

**Option 1**: Find and download that protocol binary from the [v4 Chain Releases](https://github.com/dydxprotocol/v4-chain/releases/) page.

> For example, for protocol version 5.0.5 on an AMD system, download `dydxprotocold-v5.0.5-linux-amd64.tar.gz`.

**Option 2**: Download the binary with `curl`, replacing the version numbers and architecture of the package as needed:

```
# curl example for protocol version 5.0.5 on AMD64 architecture
curl -L -O https://github.com/dydxprotocol/v4-chain/releases/download/protocol/v5.0.5/dydxprotocold-v5.0.5-linux-amd64.tar.gz
```

### Move `dydxprotocold` to your Cosmovisor `/genesis` directory

After you download the binary, moving `dydxprotocold` into your Cosmovisor data directory allows you to use Cosmovisor for no-downtime binary upgrades. To extract, rename, and move the file to your Cosmovisor data directory, run the following commands:

```
# Example for AMD64 architecture
sudo tar -xzvf dydxprotocold-v5.0.5-linux-amd64.tar.gz # Extract the file
sudo mv ./build/dydxprotocold-v5.0.5-linux-amd64 ./.dydxprotocol/cosmovisor/genesis/bin/dydxprotocold # Move the file to /.dydxprotocol and rename it
rm dydxprotocold-v5.0.5-linux-amd64.tar.gz # Delete the installer package
rm -rf build # Delete the now-empty /build directory
```

Add the `dydxprotocold` directory to your system `$PATH`:

`echo 'export PATH=$PATH:$HOME/.dydxprotocol/cosmovisor/genesis/bin' >> $HOME/.bashrc # Write to your .bashrc profile`

### Initialize your node

To initialize your node, provide the ID of the chain to which you want to connect and create a name for your node. The dYdX home directory is created in `$HOME/.dydxprotocol` by default. Replace the example values `dydx-mainnet-1` and `my-node` with your own and run the following command:

```
# Example for DYDX token holders on mainnet
dydxprotocold init --chain-id=dydx-mainnet-1 my-node
```

When you initialize your node, `dydxprotocold` returns your default node configuration in JSON.

### Update your node configuration with a list of seed nodes

A seed node acts as an address book and helps your node join the network. To update `config.toml` with a list of seed nodes, run the following command:

```
# Example for DYDX token holders on mainnet
SEED_NODES=("ade4d8bc8cbe014af6ebdf3cb7b1e9ad36f412c0@seeds.polkachu.com:23856", 
"df1f145848d253800d4e4216e8793158688912f1@seeds.kingnodes.com:23856", 
"d8e106274b24ec64ce724a611def6a3637226745@dydx-mainnet-seed.bwarelabs.com:36656",
"20e1000e88125698264454a884812746c2eb4807@seeds.lavenderfive.com:23856",
"c2c2fcb5e6e4755e06b83b499aff93e97282f8e8@tenderseed.ccvalidators.com:26401",
"a9cae4047d5c34772442322b10ef5600d8e54900@dydx-mainnet-seednode.allthatnode.com:26656",
"802607c6db8148b0c68c8a9ec1a86fd3ba606af6@64.227.38.88:26656",
"ebc272824924ea1a27ea3183dd0b9ba713494f83@dydx-mainnet-seed.autostake.com:27366"
)
 
sed -i 's/seeds = ""/seeds = "'"${SEED_NODES[*]}"'"/' $HOME/.dydxprotocol/config/config.toml
```

The preceding command updates the `seeds` variable of `config.toml` with the list you provide.

### Use a snapshot as your node's initial state

Using snapshots to restore or sync your full node's state saves time and effort. Using a snapshot avoids replaying all the blocks from genesis and does not require multiple binary versions for network upgrades. Instead, your node uses the snapshot as its initial state.

#### Clear your data directory

If you already have a data directory at `$HOME/.dydxprotocol/data`, you must clear it before installing a snapshot, which comes with its own data directory. To clear your data directory while retaining files you need, follow these steps:

First, make a backup copy of `priv_validator_state.json` in your `.dydxprotocol` directory by running the following command:

```
# Make a copy of priv_validator_state.json and append .backup
cp $HOME/.dydxprotocol/data/priv_validator_state.json $HOME/.dydxprotocol/priv_validator_state.json.backup
```

Next, confirm the following:

*   A backup file, `priv_validator_state.json.backup`, exists in your current directory.
*   The original `priv_validator_state.json` exists in the `/data` directory to be deleted.
*   No other files exist in the `/data` directory to be deleted.

```
ls $HOME/.dydxprotocol # Confirm that the backup exists in /.dydxprotocol
ls $HOME/.dydxprotocol/data # Confirm that only priv_validator_state.json exists in /data
```

Finally, to clear the data directory, removing it and all files inside, run the following command:

```
# WARNING: This command recursively deletes files and directories in the dydxprotocol /data directory. Make sure you know what you are deleting before running the command.
rm -rf $HOME/.dydxprotocol/data
```

Installing a snapshot will create a new `/data` directory.

#### Install the Snapshot

To download and extract the snapshot contents to the default dydxprotocol home directory, first **change directories into /.dydxprotocol**. To change directories, run the following command:

`cd $HOME/.dydxprotocol`

Next, find a provider for your use case on the [Snapshot Service](https://docs.dydx.xyz/nodes/resources#snapshot-service) page. Use the provider's instructions to download the snapshot into your `$HOME/.dydxprotocol` directory.

> For example, if you are connecting to `dydx-mainnet-1`, you may use the provider [Polkachu](https://polkachu.com/tendermint_snapshots/dydx). In most cases, you can run `wget <snapshot-web-address>`.

Next, run the following command in your `$/HOME/.dydxprotocol` directory, replacing the example value `your-snapshot-filename`:

`lz4 -dc < your-snapshot-filename.tar.lz4 | tar xf -`

Extracting the snapshot creates a new `/data` folder in your current directory, `.dydxprotocol`.

Next, use the backup file `priv_validator_state.json.backup` you created to reinstate `/data/priv_validator_state.json` with the following command:

`mv $HOME/.dydxprotocol/priv_validator_state.json.backup $HOME/.dydxprotocol/data/priv_validator_state.json`

Finally, **change directories back to your `$HOME` directory for the rest of the procedure**. Run the following command:

`cd $HOME`

When you start your full node, it will automatically use the snapshot in your data directory to begin syncing your full node's state with the network.

### Create a system service to start your full node automatically

To create a `systemd` service that starts your full node automatically, run the following commands:

```
sudo tee /etc/systemd/system/dydxprotocold.service > /dev/null << EOF
[Unit]
Description=dydxprotocol node service
After=network-online.target
 
[Service]
User=$USER
ExecStart=/$HOME/go/bin/cosmovisor run start --non-validating-full-node=true
WorkingDirectory=$HOME/.dydxprotocol
Restart=always
RestartSec=5
LimitNOFILE=4096
Environment="DAEMON_HOME=$HOME/.dydxprotocol"
Environment="DAEMON_NAME=dydxprotocold"
Environment="DAEMON_ALLOW_DOWNLOAD_BINARIES=false"
Environment="DAEMON_RESTART_AFTER_UPGRADE=true"
Environment="UNSAFE_SKIP_BACKUP=true"
 
[Install]
WantedBy=multi-user.target
EOF
 
sudo systemctl daemon-reload
sudo systemctl enable dydxprotocold
```

The system service definition above holds environment variables. When you start it, the service will run the command `/$HOME/go/bin/cosmovisor run start --non-validating-full-node=true`.

> The flag `--non-validating-full-node` is required. It disables the functionality intended for validator nodes and enables additional logic for reading data.

### Start the service

To start your node using the `systemd` service that you created, run the following command:

`sudo systemctl start dydxprotocold`

When you want to stop the service, run the following command:

`sudo systemctl stop dydxprotocold`

When you start your full node it must sync with the history of the network. If you initialized your full node using a snapshot, your node must update its state only with blocks created after the snapshot was taken. If your node's state is empty, it must sync with the entire history of the network.

### Check your service logs to confirm that your node is running

`sudo journalctl -u dydxprotocold -f`

If your system service `dydxprotocold` is running, the preceding command streams updates from your node to your command line. Press `Ctrl + C` to stop viewing updates.

Finally, confirm that your full node is properly synchronized by comparing its current block to the dYdX Chain:

*   To find the network's current block, see the **Block Height** of your network with a block explorer, such as [mintscan.io](https://www.mintscan.io/dydx).
*   To find your full node's height, query your node with the following command:

`curl localhost:26657/status`

When your full node's latest block is the same as the network's latest block, your full node is ready to participate in the network.

When your full node is up to date with the network, you can use it to read live data and configure additional settings. Learn more on the [Optimizing Your Full Node](https://docs.dydx.xyz/nodes/running-node/optimize) and [Full Node Streaming](https://docs.dydx.xyz/nodes/full-node-streaming)pages.
Title: Optimize Your Full Node

URL Source: https://docs.dydx.xyz/nodes/running-node/optimize

Published Time: Tue, 21 Oct 2025 12:48:10 GMT

Markdown Content:
Optimizing your full node helps keep it online, up to date, and operating quickly. Faster nodes have an advantage over slower nodes because they tend to receive new data first and they minimize the time between placing and resolving orders. Optimize your full node by connecting to trusted nodes, taking precautions against falling out of sync with the network, and configuring storage settings.

Prerequisites
-------------

You need a running, non-validating full node that is connected to a network.

*   If you created a system service for your node by following the instructions on the previous page, [Set Up a Full Node](https://docs.dydx.xyz/nodes/running-node/setup), start your node with the following command:

`stystemctl start dydxprotocold` 
*   To start your node with Cosmovisor or with the `dydxprotocold` binary, you must include the flag `--non-validating-full-node=true`. The flag disables the functionality intended for validator nodes and enables additional logic for reading data. Your CLI may prompt you to configure additional variables in your environment or include them in your command.

To start your node with Cosmovisor, run the following command:

`cosmovisor run start --non-validating-full-node=true` 
To start your node with `dydxprotocold`, run the following command:

`dydxprotocold run start --non-validating-full-node=true` 

Save a List of Trusted Nodes
----------------------------

Specify a list of healthy, stable nodes that you trust. Your node prioritizes connecting to those nodes, speeding up the process of connecting or re-connecting to the network. Connecting directly with a peer node is faster than connecting to a seed node and then finding new peers.

### Save a List of Persistent Peers

You can save a list of healthy, stable nodes in the `persistent_peers` field of your `config.toml` file.

Request a list of healthy peers for your deployment from a [Live Peer Node](https://docs.dydx.xyz/nodes/resources#live-peer-node-providers) provider.

From the list of healthy peers that you retrieve from peer node provider, choose any 5 for your node to query for the latest state. Add a comma-separated list of those peer addresses to the `persistent_peers` field in your `config.toml`, like in the following example:

```
# config.toml
# Example values from Polkachu for dydx-mainnet-1
persistent_peers=83c299de2052db247f08422b6592e1383dd7a104@136.243.36.60:23856,1c64b35055d34ff3dd199bb4a5a3ae46b9c10c89@3.114.126.71:26656,3651c82a89f8f4d6fc30fb27b91159f0de092031@202.8.9.134:26656,580ec248de1f41d4e50abe132b7838348db55b80@176.9.144.40:23856,febe75fb6e70a60ce6344b82ff14903bcb53a209@38.122.229.90:26656
```

### Replace Your Address Book File

As an alternative to persistent peers, you can replace your node's local address book with the latest address book from a trusted provider. The address book file contains the latest connection information for peers from that provider.

Download an up-to-date `addrbook.json` file for your deployment from an [Address Book](https://docs.dydx.xyz/nodes/resources#address-book-providers) provider.

Save it in your `/.dydxprotocol/config` directory, replacing the existing `addrbook.json` file.

Prepare to Restore Your Node
----------------------------

To minimize downtime in case your node falls out of sync, make preparations to restore your node quickly.

Your full node can fall out of sync with the rest of the network for a variety of reasons, including a bad software upgrade, unexpected node crashes, or human operational error. To re-sync with the network, your full node needs to replay the history of the network, which can take a long time.

You can speed up the re-syncing process significantly by providing your node with a snapshot. A snapshot contains a compressed copy of the application state at the time the snapshot was taken. If your node falls out of sync, a snapshot allows it to recover to that saved state before replaying the rest of the history of the network, saving you time.

### Configure Your Node's State Sync Setting

You can use state sync, a configuration setting that allows your node to retrieve a snapshot from the network, to ensure that your node can be restored quickly if it falls out of sync.

To use state sync for quick recovery in case your node falls out of sync, follow the instructions for your deployment from a [State Sync](https://docs.dydx.xyz/nodes/resources#state-sync-service) service.

### Save a Snapshot on Your System

As an alternative to state sync, you can use a snapshot that you have saved on your node's system to restore your node if it falls out of sync.

To save a snapshot on your system for quick recovery in case your node falls out of sync, install a snapshot for your deployment from a [Snapshot Service](https://docs.dydx.xyz/nodes/resources#snapshot-service).

Configure a Pruning Strategy
----------------------------

To reduce the amount of storage your node requires, dYdX recommends the following pruning setting, configured in your `app.toml` file:

```
# app.toml
pruning = "everything" # 2 latest states will be kept; pruning at 10 block intervals
```

However, if you want to use your node to query historical data, configure a custom pruning strategy to retain more states. Retaining more states increases storage requirements.
Title: Running a Validator

URL Source: https://docs.dydx.xyz/nodes/running-node/running-a-validator

Markdown Content:
💡Note: failure to set up below configurations on a validator node may compromise chain functionality.

Disabled ETH bridge
-------------------

For the chain to process bridge transactions from Ethereum, Ethereum testnet, or other chain that supports the `eth_getLogs` RPC method, the bridge daemon queries an RPC endpoint for logs emitted by the bridge contract. By default, a node will use a public testnet endpoint that may have rate-limiting, low reliability, or other restricted functionality.

As a validator run the flags `--bridge-daemon-enabled=false` in the command you run when starting the node, since the bridge has been disabled

Connect Sidecar
---------------

Starting in `v5.0.0`, running a validating full node requires a Skip Protocol's Connect Sidecar to be run in order to fetch Oracle prices. The sidecar should be started before upgrading from `v4` to `v5`. Instructions to start Connect Sidecar can be found [here](https://docs.skip.build/connect/validators/quickstart).

Support issues with Skip's Sidecar should be directed [here](https://discord.gg/7hxEThEaRQ).

You can find the required version of the Connect sidecar listed in the `dYdX Blockchain` section [here](https://docs.skip.build/connect/validators/quickstart#run-connect-sidecar).

Instructions on upgrading sidecar can be found [here](https://docs.dydx.xyz/nodes/upgrades/upgrading-sidecar).
Title: Snapshots

URL Source: https://docs.dydx.xyz/nodes/running-node/snapshots

Markdown Content:
Snapshots – dYdX Documentation

===============

[Skip to content](https://docs.dydx.xyz/nodes/running-node/snapshots#vocs-content)

[![Image 1: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Guide

API

Concepts

Nodes

Running Your Node

[Hardware Requirements](https://docs.dydx.xyz/nodes/running-node/hardware-requirement)[Required Node Configs](https://docs.dydx.xyz/nodes/running-node/required-node-configs)[Setup](https://docs.dydx.xyz/nodes/running-node/setup)[Optimize](https://docs.dydx.xyz/nodes/running-node/optimize)[Running a Validator](https://docs.dydx.xyz/nodes/running-node/running-a-validator)[Snapshots](https://docs.dydx.xyz/nodes/running-node/snapshots)[Peering with Gateway](https://docs.dydx.xyz/nodes/running-node/peering-with-gateway)[Voting](https://docs.dydx.xyz/nodes/running-node/voting)

[Node Streaming](https://docs.dydx.xyz/nodes/full-node-streaming)

Upgrades

[Network Constants](https://docs.dydx.xyz/nodes/network-constants)[Resources](https://docs.dydx.xyz/nodes/resources)

Policies

Search...

[![Image 2: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

[![Image 3: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Menu

Snapshots

On this page

Snapshots[](https://docs.dydx.xyz/nodes/running-node/snapshots#snapshots)
=========================================================================

Services that provide snapshots for the network can be found [here](https://docs.dydx.xyz/nodes/resources#snapshot-service). These snapshots will be used as a backup point in case an upgrade fails or a new node wants to start up and does not want to start from block 1 to catchup.

Last updated: 9/19/25, 5:57 AM

[Running a Validator Previous shift←](https://docs.dydx.xyz/nodes/running-node/running-a-validator)[Peering with Gateway Next shift→](https://docs.dydx.xyz/nodes/running-node/peering-with-gateway)
Title: Peering Directly with Order Gateway

URL Source: https://docs.dydx.xyz/nodes/running-node/peering-with-gateway

Markdown Content:
For improved order latency of the network, the community might spin up an order gateway node to directly peer with. A chain coordination party may share this in the form of `$gateway_node_id@$gateway_ip_address:$port`.

There are 2 options to peer directly with the gateway node:

Option A: Gateway -> Validator
------------------------------

*   Share the full peering info of your validator node (`node_id@ip_address:port`) with the coordination party, which can be added as a `persistent_peer` to the gateway node. It's important that raw IP address (as opposed to a loadbalancer URL) of the validator node (as opposed to a sentry node) is shared. This ensures that the a direction connection can be maintained across node restarts.
    *   If your IP or node ID changes due to node migration, please inform the coordination party.

*   Add the gateway `node_id` as a private and unconditional peer. This ensure that the gateway node is not subject to regualr peer # limits, and is not broadcasted to the rest of the network.

```
--p2p.private_peer_ids="$gateway_node_id,..."
--p2p.unconditional_peer_ids="$gateway_node_id,..."
```

Option B: Validator -> Gateway
------------------------------

*   Share the `node_id` (IP not required) of your validator node with the coordination party. It's important to share the `node_id` of the validator node, as opposed to a sentry node. This can be added to the gateway node as `unconditional_peer`.
*   Add the gateway node as a persistent and private peer to the validator node:

```
--p2p.private_peer_ids="$gateway_node_id,..."
--p2p.persistent_peers="$gateway_node_id@$gateway_ip_address:$port,..."
```

CometBFT [documentation](https://docs.cometbft.com/v0.38/spec/p2p/legacy-docs/config) on P2P configs
Title: Voting

URL Source: https://docs.dydx.xyz/nodes/running-node/voting

Markdown Content:
Save your Chain ID in `dydxprotocold` config
--------------------------------------------

Save the [chain-id](https://docs.dydx.xyz/nodes/network-constants#chain-id). This will make it so you do not have to manually pass in the chain-id flag for every CLI command.

`dydxprotocold config set client chain-id [chain_id]`

View the status of a proposal
-----------------------------

To view the status of a proposal, use the following command:

`dydxprotocold query gov proposal [proposal_id]`

The status of the proposal will be returned:

```
deposit_end_time: "2023-04-02T19:21:27.467932675Z"
final_tally_result:
  abstain_count: "0"
  no_count: "0"
  no_with_veto_count: "0"
  yes_count: "0"
id: "1"
messages:
- '@type': /cosmos.upgrade.v1beta1.MsgSoftwareUpgrade
  authority: dydx10d07y265gmmuvt4z0w9aw880jnsr700jnmapky
  plan:
    height: "60400"
    info: ""
    name: v0.1.0
    time: "0001-01-01T00:00:00Z"
    upgraded_client_state: null
metadata: ""
proposer: dydx199tqg4wdlnu4qjlxchpd7seg454937hjrknju4
status: PROPOSAL_STATUS_VOTING_PERIOD
submit_time: "2023-03-31T19:21:27.467932675Z"
summary: This is a proposal to schedule v0.1.0 software upgrade at block height 60400,
  estimated to occur on Tuesday April 4th at 1PM EDT.
title: dYdX Protocol v1.0.0 Upgrade
total_deposit:
- amount: "10000000"
  denom: stake
voting_end_time: "2023-03-31T19:22:27.467932675Z"
voting_start_time: "2023-03-31T19:21:27.467932675Z"
```

Voting for a proposal
---------------------

To vote for a governance proposal, use the following command:

`dydxprotocold tx gov vote [proposal_id] [option] --from [key]`

The option can be either `Yes`, `No`, `NoWithVeto`, `Abstain`. See [here](https://docs.cosmos.network/v0.47/modules/gov#option-set) for the descriptions of the these options.

To see the votes
----------------

`dydxprotocold query gov votes [proposal_id]`

```
pagination:
  next_key: null
  total: "0"
votes:
- metadata: ""
  options:
  - option: VOTE_OPTION_YES
    weight: "1.000000000000000000"
  proposal_id: "1"
  voter: dydx199tqg4wdlnu4qjlxchpd7seg454937hjrknju4
...
```

To see the tally of votes
-------------------------

To query tally of votes on a proposal:

`dydxprotocold query gov tally [proposal_id]`

This will return something like:

```
abstain_count: "0"
no_count: "0"
no_with_veto_count: "0"
yes_count: "0"
```
Title: gRPC Streaming Example

URL Source: https://docs.dydx.xyz/nodes/full-node-streaming/example

Published Time: Tue, 21 Oct 2025 21:59:12 GMT

Markdown Content:
gRPC Streaming Example – dYdX Documentation

===============

[Skip to content](https://docs.dydx.xyz/nodes/full-node-streaming/example#vocs-content)

[![Image 1: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Guide

API

Concepts

Nodes

Running Your Node

[Hardware Requirements](https://docs.dydx.xyz/nodes/running-node/hardware-requirement)[Required Node Configs](https://docs.dydx.xyz/nodes/running-node/required-node-configs)[Setup](https://docs.dydx.xyz/nodes/running-node/setup)[Optimize](https://docs.dydx.xyz/nodes/running-node/optimize)[Running a Validator](https://docs.dydx.xyz/nodes/running-node/running-a-validator)[Snapshots](https://docs.dydx.xyz/nodes/running-node/snapshots)[Peering with Gateway](https://docs.dydx.xyz/nodes/running-node/peering-with-gateway)[Voting](https://docs.dydx.xyz/nodes/running-node/voting)

[Node Streaming](https://docs.dydx.xyz/nodes/full-node-streaming)

[Example](https://docs.dydx.xyz/nodes/full-node-streaming/example)

Upgrades

[Network Constants](https://docs.dydx.xyz/nodes/network-constants)[Resources](https://docs.dydx.xyz/nodes/resources)

Policies

Search...

[![Image 2: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

[![Image 3: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Menu

Example

On this page

[Ask in ChatGPT](https://chatgpt.com/?hints=search&q=Please%20research%20and%20analyze%20this%20page%3A%20https%3A%2F%2Fdocs.dydx.xyz%2Fnodes%2Ffull-node-streaming%2Fexample%20so%20I%20can%20ask%20you%20questions%20about%20it.%20Once%20you%20have%20read%20it%2C%20prompt%20me%20with%20any%20questions%20I%20have.%20Do%20not%20post%20content%20from%20the%20page%20in%20your%20response.%20Any%20of%20my%20follow%20up%20questions%20must%20reference%20the%20site%20I%20gave%20you.)

On this page
------------

*   [Install dependencies](https://docs.dydx.xyz/nodes/full-node-streaming/example#install-dependencies)
*   [Establish a connection](https://docs.dydx.xyz/nodes/full-node-streaming/example#establish-a-connection)
*   [Streaming](https://docs.dydx.xyz/nodes/full-node-streaming/example#streaming)
*   [Maintaining Orderbook and Subaccount State](https://docs.dydx.xyz/nodes/full-node-streaming/example#maintaining-orderbook-and-subaccount-state)

    *   [Snapshots](https://docs.dydx.xyz/nodes/full-node-streaming/example#snapshots)
    *   [Orderbook Management](https://docs.dydx.xyz/nodes/full-node-streaming/example#orderbook-management)

*   [Additional logic](https://docs.dydx.xyz/nodes/full-node-streaming/example#additional-logic)

gRPC Streaming Example[](https://docs.dydx.xyz/nodes/full-node-streaming/example#grpc-streaming-example)
========================================================================================================

[Indexer-based orderbook streaming](https://docs.dydx.xyz/interaction/data/watch-orderbook), due to the increased latency introduced by the Indexer, can cause issues like more outdated orders or a crossed orderbook. In a full node, the orderbook available will be more up-to-date and should be preferred over the Indexer-based solution. This requires a full node with [gRPC streaming enabled](https://docs.dydx.xyz/nodes/full-node-streaming).

While more up-to-date than the Indexer, the orderbook state can vary slightly between nodes due to dYdX's offchain orderbook design.

In this example, we'll guide on how to connect and handle the gRPC data in order to enable use-cases such as orderbook watching. While full node streaming is provided both using gRPC and WebSockets, we'll focus here on gRPC-based streaming due to its higher efficiency.

**Full Example**
This guide is only a general walkthrough of the important methods on how to establish and maintain a gRPC connection, and maintain the orderbook state. For the worked example see the [repository](https://github.com/dydxprotocol/grpc-stream-client) (Python).

Install dependencies[](https://docs.dydx.xyz/nodes/full-node-streaming/example#install-dependencies)
----------------------------------------------------------------------------------------------------

gRPC uses structured and serialized data using [Protocol Buffers](https://en.wikipedia.org/wiki/Protocol_Buffers). For Python, install the package [`v4-proto`](https://pypi.org/project/v4-proto/) which already contains the messages and generated code used in gRPC. This is the main dependency used in this guide, allowing us to deserialize the incoming stream messages.

Dependency list
The full dependency list used in this guide.

Terminal

```
grpcio>=1.67.0
grpcio-tools==1.64.1
protobuf==5.28.1
PyYAML==6.0.1
sortedcontainers==2.4.0
v4-proto==6.0.8
```

Establish a connection[](https://docs.dydx.xyz/nodes/full-node-streaming/example#establish-a-connection)
--------------------------------------------------------------------------------------------------------

With a full node with gRPC streaming available, we can now try to establish a connection to it. We'll need to define a gRPC configuration to maintain an healthy connection. Lets also define here the CLOB pairs IDs (markets) that we are interested in, as well as the relevant subaccounts.

Python

```
import grpc
from v4_proto.dydxprotocol.clob.query_pb2 import StreamOrderbookUpdatesRequest
from v4_proto.dydxprotocol.clob.query_pb2_grpc import QueryStub
from v4_proto.dydxprotocol.subaccounts.subaccount_pb2 import SubaccountId
 
GRPC_OPTIONS = [
    # Send keepalive ping every 30 seconds
    ("grpc.keepalive_time_ms", 3000),
    # Wait 10 seconds for ping ack before considering the connection dead
    ("grpc.keepalive_timeout_ms", 1000,),
    # Allow keepalive pings even when there are no calls
    ("grpc.keepalive_permit_without_calls", True,),
    # Minimum allowed time between pings
    ("grpc.http2.min_time_between_pings_ms", 3000,),
    # Minimum allowed time between pings with no data
    ("grpc.http2.min_ping_interval_without_data_ms", 3000,),
]
 
endpoint = "your-node-address:9090"
clob_pair_ids = [0, 1] # ETH-USD
subaccount_ids = [] # All subaccounts
 
# Establish async connection 
async with grpc.aio.insecure_channel(endpoint, GRPC_OPTIONS) as channel:
    tasks = [
        listen_to_grpc_stream(
            channel,
            clob_pair_ids,
            subaccount_ids,
            feed_handler,
        ),
    ]
    await asyncio.gather(*tasks)
```

Streaming[](https://docs.dydx.xyz/nodes/full-node-streaming/example#streaming)
------------------------------------------------------------------------------

The streaming function `listen_to_grpc_stream()` processes the continuous stream of orderbook updates. Each message contains batched updates that must be processed sequentially to maintain correct state.

Python

```
async def listen_to_grpc_stream(
    channel: grpc.Channel,
    clob_pair_ids: List[int],
    subaccount_ids: List[str],
    feed_handler: FeedHandler,
):
    """Subscribe to gRPC stream and handle orderbook updates."""
    stub = QueryStub(channel)
    
    # Parse subaccount ids (format: owner_address/subaccount_number)
    subaccount_protos = [
        SubaccountId(owner=sa.split('/')[0], number=int(sa.split('/')[1])) 
        for sa in subaccount_ids
    ]
    
    request = StreamOrderbookUpdatesRequest(
        clob_pair_id=clob_pair_ids, 
        subaccount_ids=subaccount_protos
    )
    
    async for response in stub.StreamOrderbookUpdates(request):
        fill_events = feed_handler.handle(response)
        # Process fills and other updates
        for fill in fill_events:
            print(f"Fill: {fill.quantums} @ {fill.subticks}")
```

Maintaining Orderbook and Subaccount State[](https://docs.dydx.xyz/nodes/full-node-streaming/example#maintaining-orderbook-and-subaccount-state)
------------------------------------------------------------------------------------------------------------------------------------------------

Lets add a component `FeedHandler` that maintains local state by processing streaming updates. It will handle different message types and ensure state consistency.

Python

```
class FeedHandler:
    def __init__(self):
        self.books: Dict[int, LimitOrderBook] = {}
        self.subaccounts: Dict[SubaccountId, StreamSubaccount] = {}
        self.has_seen_first_snapshot = False
    
    def handle(self, message: StreamOrderbookUpdatesResponse) -> List[Fill]:
        """Handle incoming stream messages and update state."""
        collected_fills = []
        
        for update in message.updates:
            update_type = update.WhichOneof('update_message')
            
            if update_type == 'orderbook_update':
                self._handle_orderbook_update(update.orderbook_update)
            elif update_type == 'order_fill':
                fills = self._handle_fills(update.order_fill, update.exec_mode)
                collected_fills += fills
            elif update_type == 'subaccount_update':
                self._handle_subaccounts(update.subaccount_update)
                
        return collected_fills
```

### Snapshots[](https://docs.dydx.xyz/nodes/full-node-streaming/example#snapshots)

Snapshots provide the complete current state and serve as the foundation for processing subsequent incremental updates. The client should wait for snapshots before processing any other messages to ensure state consistency.

> Discard order messages until you receive a `StreamOrderbookUpdate` with `snapshot` set to `true`. This message contains the full orderbook state for each clob pair.

> Similarly, discard subaccount messages until you receive a `StreamSubaccountUpdate` with `snapshot` set to `true`. This message contains the full subaccount state for each subscribed subaccount.

```
def _handle_orderbook_update(self, update: StreamOrderbookUpdate):
    """Handle orderbook snapshots and incremental updates."""
    # Skip messages until the first snapshot is received
    if not self.has_seen_first_snapshot and not update.snapshot:
        return
    
    # Skip subsequent snapshots
    if update.snapshot and self.has_seen_first_snapshot:
        logging.warning("Skipping subsequent snapshot")
        return
    
    if update.snapshot:
        # This is a new snapshot of the book state
        if not self.has_seen_first_snapshot:
            self.has_seen_first_snapshot = True
    
    # Process each update in the batch
    for u in update.updates:
        update_type = u.WhichOneof('update_message')
        
        if update_type == 'order_place':
            self._handle_order_place(u.order_place)
        elif update_type == 'order_update':
            self._handle_order_update(u.order_update)
        elif update_type == 'order_remove':
            self._handle_order_remove(u.order_remove)
 
def _handle_subaccounts(self, update: StreamSubaccountUpdate):
    """Handle subaccount snapshots and updates."""
    parsed_subaccount = parse_subaccounts(update)
    subaccount_id = parsed_subaccount.subaccount_id
    
    if update.snapshot:
        # Skip subsequent snapshots
        if subaccount_id in self.subaccounts:
            logging.warning(f"Saw multiple snapshots for subaccount {subaccount_id}")
            return
        self.subaccounts[subaccount_id] = parsed_subaccount
    else:
        # Skip messages until the first snapshot is received
        if subaccount_id not in self.subaccounts:
            return
        # Update the existing subaccount
        existing_subaccount = self.subaccounts[subaccount_id]
        existing_subaccount.perpetual_positions.update(parsed_subaccount.perpetual_positions)
        existing_subaccount.asset_positions.update(parsed_subaccount.asset_positions)
```

### Orderbook Management[](https://docs.dydx.xyz/nodes/full-node-streaming/example#orderbook-management)

The orderbook is implemented as a Level 3 (L3) order book that maintains individual orders with their full details. This provides maximum granularity for trading applications that need to track specific orders and their execution.

Order Data

```
from dataclasses import dataclass
from typing import Dict, Iterator, Optional
from sortedcontainers import SortedDict
 
@dataclass(frozen=True)  # frozen=True allows use as dict keys
class OrderId:
    """Unique identifier for orders within a CLOB pair."""
    owner_address: str        # Account that placed the order
    subaccount_number: int    # Subaccount index within the account  
    client_id: int           # Client-assigned order ID (can be reused)
    order_flags: int         # Order type flags (conditional, short-term, etc.)
 
@dataclass
class Order:
    """Individual order with pricing and quantity information."""
    order_id: OrderId
    is_bid: bool             # True for buy orders, False for sell orders
    original_quantums: int   # Original order size (integer, needs conversion)
    quantums: int           # Remaining size after fills (integer, needs conversion)
    subticks: int           # Price level (integer, needs conversion)
```

Lets implement an efficient Orderbook data structure named `LimitOrderBook` suitable for high-frequency trading.

Orderbook

```
class LimitOrderBook:
    """
    Level 3 orderbook with O(log N) insertion, O(1) updates and removal.
    
    Architecture:
    - SortedDict maps price levels to order queues
    - Each price level is a doubly-linked list (FIFO order execution)
    - Hash map provides O(1) order lookup by OrderId
    """
    
    def __init__(self):
        # Fast order lookup by ID
        self.oid_to_order_node: Dict[OrderId, ListNode] = {}
        
        # Price-ordered asks (lowest price first)
        self._asks: SortedDict[int, DoublyLinkedList] = SortedDict()
        
        # Price-ordered bids (highest price first)  
        self._bids: SortedDict[int, DoublyLinkedList] = SortedDict(lambda x: -x)
    
    def add_order(self, order: Order) -> Order:
        """
        Add order to the end of its price level queue.
        
        Orders at the same price level execute in time priority (FIFO).
        New orders are always placed at the back of the queue.
        """
        # Determine which side of the book
        book_side = self._bids if order.is_bid else self._asks
        
        # Get or create the price level
        level = self._get_or_create_level(order.subticks, book_side)
        
        # Add to end of price level queue and index for fast lookup
        order_node = level.append(order)
        self.oid_to_order_node[order.order_id] = order_node
        
        return order
    
    def remove_order(self, oid: OrderId) -> Order:
        """
        Remove order from book and clean up empty price levels.
        
        Returns the removed order for processing (e.g., logging cancellations).
        """
        # Find and remove the order node
        order_node = self.oid_to_order_node.pop(oid)
        order = order_node.data
        
        # Remove from the appropriate price level
        book_side = self._bids if order.is_bid else self._asks
        level: DoublyLinkedList = book_side[order.subticks]
        level.remove(order_node)
        
        # Clean up empty price levels to save memory
        if level.head is None:
            del book_side[order.subticks]
        
        return order
    
    def get_order(self, oid: OrderId) -> Optional[Order]:
        """O(1) order lookup by ID."""
        node = self.oid_to_order_node.get(oid)
        return node.data if node else None
    
    def asks(self) -> Iterator[Order]:
        """Iterate asks from best (lowest) to worst (highest) price."""
        for price, level in self._asks.items():
            for order in level:  # Time priority within price level
                yield order
    
    def bids(self) -> Iterator[Order]:
        """Iterate bids from best (highest) to worst (lowest) price.""" 
        for price, level in self._bids.items():
            for order in level:  # Time priority within price level
                yield order
    
    @staticmethod
    def _get_or_create_level(subticks: int, book_side: SortedDict) -> DoublyLinkedList:
        """Lazily create price levels as orders arrive."""
        if subticks not in book_side:
            book_side[subticks] = DoublyLinkedList()
        return book_side[subticks]
```

Each price level maintains orders in a doubly-linked list for efficient insertion and removal.

Order Queue

```
class ListNode:
    """Node in the doubly-linked list representing an order."""
    def __init__(self, data):
        self.data = data      # The Order object
        self.prev = None      # Previous order in queue
        self.next = None      # Next order in queue
 
class DoublyLinkedList:
    """
    FIFO queue for orders at the same price level.
    
    Provides O(1) append and remove operations essential
    for high-frequency order book updates.
    """
    
    def __init__(self):
        self.head = None  # First order (next to execute)
        self.tail = None  # Last order (most recently added)
    
    def append(self, data) -> ListNode:
        """Add new order to the end of the queue."""
        new_node = ListNode(data)
        
        if self.head is None:
            # First order at this price level
            self.head = self.tail = new_node
        else:
            # Add to end, maintaining FIFO order
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
            
        return new_node
    
    def remove(self, node_to_remove: ListNode):
        """Remove specific order from anywhere in the queue."""
        # Update previous node's forward link
        if node_to_remove.prev:
            node_to_remove.prev.next = node_to_remove.next
        else:
            self.head = node_to_remove.next
        
        # Update next node's backward link  
        if node_to_remove.next:
            node_to_remove.next.prev = node_to_remove.prev
        else:
            self.tail = node_to_remove.prev
        
        # Clean up the removed node
        node_to_remove.prev = node_to_remove.next = None
```

Orders progress through a lifecycle of placement, updates, and removal. Your client must handle each stage correctly to maintain accurate book state.

Order Management

```
def _handle_order_place(self, order_place: OrderPlaceV1) -> int:
    """
    Insert new orders at the end of their price level queue.
    Track both initial quantity and cumulative filled amount.
    """
    order = helpers.parse_indexer_order(order_place.order)
    clob_pair_id = order_place.order.order_id.clob_pair_id
    book = self._get_book(clob_pair_id)
    
    # Verify order doesn't already exist (should see remove before place)
    if book.get_order(order.order_id) is not None:
        raise AssertionError(f"Order {order.order_id} already exists")
    
    # Store initial quantums for fill tracking
    order.original_quantums = order.quantums
    book.add_order(order)
    return clob_pair_id
 
def _handle_order_update(self, order_update: OrderUpdateV1) -> int:
    """
    Update an order's total filled amount.
    
    Note: total_filled_quantums is cumulative, not incremental.
    Remaining quantity = original_quantums - total_filled_quantums
    """
    clob_pair_id = order_update.order_id.clob_pair_id
    oid = helpers.parse_indexer_oid(order_update.order_id)
    order = self._get_book(clob_pair_id).get_order(oid)
    
    if order is None:
        # Order may not exist yet due to message ordering
        return clob_pair_id
    
    # Calculate remaining quantity after fills
    order.quantums = order.original_quantums - order_update.total_filled_quantums
    return clob_pair_id
 
def _handle_order_remove(self, order_remove: OrderRemoveV1) -> int:
    """
    Remove orders from the book.
    
    Removal reasons include:
    - User cancellation
    - Order expiry (Good-Til-Block/Good-Til-BlockTime)
    - Complete fill
    - Best-effort cancellation (order may still fill until expiry)
    """
    clob_pair_id = order_remove.order_id.clob_pair_id
    oid = helpers.parse_indexer_oid(order_remove.order_id)
    book = self._get_book(clob_pair_id)
    
    # Remove order if it exists (may have already been removed)
    if book.get_order(oid) is not None:
        book.remove_order(oid)
    
    return clob_pair_id
```

Handle both optimistic and finalized trades correctly. Optimistic fills update book state immediately, while only finalized fills should be treated as confirmed trades.

Fills and Trade Confirmation

```
def _handle_fills(self, order_fill: StreamOrderbookFill, exec_mode: int) -> List[fills.Fill]:
    """
    Process trade fills and update maker order states.
    
    Important: Use ALL ClobMatch messages to update book state (optimistic),
    but only treat execMode=7 (finalized) fills as confirmed trades.
    """
    # Skip fills until we have orderbook snapshots
    if not self.has_seen_first_snapshot:
        return []
    
    parsed_fills = fills.parse_fill(order_fill, exec_mode)
    
    for fill in parsed_fills:
        clob_pair_id = fill.clob_pair_id
        maker_oid = fill.maker
        order = self._get_book(clob_pair_id).get_order(maker_oid)
        
        if order is not None:
            # Update maker order's remaining quantity
            # fill_amounts represents total filled, not incremental
            order.quantums = order.original_quantums - fill.maker_total_filled_quantums
            
            # Log different treatment for optimistic vs finalized
            status = "finalized" if exec_mode == 7 else "optimistic"
            logging.debug(f"({status}) Fill processed: {fill.quantums} @ {fill.subticks}")
    
    return parsed_fills
 
def is_trade_finalized(fill: fills.Fill) -> bool:
    """
    Only treat fills with exec_mode=7 as consensus-confirmed trades.
    Other exec modes are optimistic and may be reverted.
    """
    return fill.exec_mode == 7
```

Additional logic[](https://docs.dydx.xyz/nodes/full-node-streaming/example#additional-logic)
--------------------------------------------------------------------------------------------

Process informational taker order messages without updating state.

Taker Orders

```
def _handle_taker_order(self, stream_taker_order: StreamTakerOrder, block_height: int):
    """
    Handle taker order messages (informational only).
    
    Taker orders are emitted when orders enter the matching engine,
    regardless of success/failure. No state updates required.
    """
    order = helpers.parse_protocol_order(stream_taker_order.order)
    
    # Log for analytics/monitoring but don't update book state
    logging.debug(f"Taker order: {order.order_id} size={order.quantums}")
    
    # Optional: Track taker order metrics
    self.taker_order_metrics.process_order(order, block_height)
```

Convert protocol integers to decimal values for display and analysis. [Fetch the market information](https://docs.dydx.xyz/indexer-client/http#get-perpetual-markets) from the Indexer, containing data required for integer conversion.

Data Conversion

```
def subticks_to_price(subticks: int, atomic_resolution: int, quantum_conversion_exponent: int) -> float:
    """
    Convert integer subticks to human-readable price.
    
    Formula: subticks * 10^(-atomic_resolution) * 10^(-quantum_conversion_exponent)
    """
    return subticks * (10 ** (-atomic_resolution - quantum_conversion_exponent))
 
def quantums_to_size(quantums: int, atomic_resolution: int) -> float:
    """
    Convert integer quantums to human-readable quantity.
    
    Formula: quantums * 10^(-atomic_resolution)
    """
    return quantums * (10 ** (-atomic_resolution))
 
def format_fill_for_display(fill: fills.Fill, market_info: dict) -> str:
    """Format fill for human consumption."""
    ar = market_info['atomicResolution']
    qce = market_info['quantumConversionExponent']
    
    price = subticks_to_price(fill.subticks, ar, qce)
    size = quantums_to_size(fill.quantums, ar)
    side = "buy" if fill.taker_is_buy else "sell"
    status = "finalized" if fill.exec_mode == 7 else "optimistic"
    
    return f"({status}) {side} {size} @ {price}"
```

Validate orderbook state consistency in order to detect any errors, here related with crossed orderbook (a bid larger than a ask).

Validate Orderbook

```
def _validate_books(self):
    """
    Validate orderbook state consistency.
    
    Each node maintains subjective state until block finalization.
    Regular validation helps detect processing errors.
    """
    for cpid, book in self.books.items():
        best_ask = next(book.asks(), None)
        best_bid = next(book.bids(), None)
        
        if best_ask and best_bid:
            if best_ask.subticks <= best_bid.subticks:
                # Crossed book indicates state error
                raise AssertionError(
                    f"Crossed book for market {cpid}: "
                    f"ask {best_ask.subticks} <= bid {best_bid.subticks}"
                )
```

Last updated: 9/19/25, 5:57 AM

[Node Streaming Previous shift←](https://docs.dydx.xyz/nodes/full-node-streaming)[Types of Upgrades Next shift→](https://docs.dydx.xyz/nodes/upgrades/types-of-upgrades)
upstream connect error or disconnect/reset before headers. reset reason: connection terminationTitle: Performing Upgrades

URL Source: https://docs.dydx.xyz/nodes/upgrades/performing-upgrades

Markdown Content:
Managing Upgrades
-----------------

Validators can choose how to run a validator and manage software upgrades according to their preferred option:

1.   Using [Cosmovisor](https://docs.dydx.xyz/cosmovisor)
2.   Manual

Voting for Upgrade Proposals
----------------------------

See [Voting](https://docs.dydx.xyz/vercel/path1/docs/pages/nodes/running-node/voting)

Releases for the dYdX Chain will use [semantic versioning](https://semver.org/). See [here](https://docs.dydx.xyz/types-of-upgrades) for details.

### ⚒️ Cosmovisor Users

#### Upgrading to a new Major/Minor Version (e.g. v0.1.0)

1.   Download the [binary](https://github.com/dydxprotocol/v4-chain) for the new release, rename the binary to `dydxprotocold`.

`mv dydxprotocold.<version>-<platform> dydxprotocold`

1.   Make sure that the new binary is executable.

`chmod 755 dydxprotocold`

1.   Create a new directory `$DAEMON_HOME/cosmovisor/upgrades/<name>/bin` where `<name>` is the URI-encoded name of the upgrade as specified in the Software Upgrade Plan.

`mkdir -p $DAEMON_HOME/cosmovisor/upgrades/<name>/bin`

1.   Place the new binary under `$DAEMON_HOME/cosmovisor/upgrades/<name>/bin` before the upgrade height.

`mv <path_to_major_version> $DAEMON_HOME/cosmovisor/upgrades/<name>/bin`

💡 **IMPORTANT**: Do this before the upgrade height, so that `cosmovisor` can make the switch.

That's it! The old binary will stop itself at the upgrade height, and `cosmovisor` will switch to the new binary automatically. For a `Plan` with name `v0.1.0`, your `cosmovisor/` directory should look like this:

```
cosmovisor/
├── current/   # either genesis or upgrades/<name>
├── genesis
│   └── bin
│       └── dydxprotocold
└── upgrades
    └── v0.1.0
        ├── bin
           └── dydxprotocold
```

#### Upgrading to a Patch Version (e.g. v0.0.2)

1.   Download the [binary](https://github.com/dydxprotocol/v4-chain/releases) for the new patch release, rename the binary to `dydxprotocold`.

`mv dydxprotocold.<version>-<platform> dydxprotocold`

1.   Make sure that the new binary is executable.

`chmod 755 dydxprotocold`

1.   Replace the binary under `$DAEMON_HOME/cosmovisor/current/bin` with the new binary.

`mv <path_to_patch_version> $DAEMON_HOME/cosmovisor/current/bin`

1.   Stop the current binary (e.g. Ctrl+C)
2.   Restart `cosmovisor`

`cosmovisor run start --p2p.seeds="[seed_node_id]@[seed_node_ip_addr]:26656" --bridge-daemon-eth-rpc-endpoint="<eth rpc endpoint>"`

### 🦾 Manual Users

#### Upgrading to a Major/Minor Version (e.g. v0.1.0)

1.   Download the [binary](https://github.com/dydxprotocol/v4-chain/releases) for the new release.
    1.   Ideally also before the upgrade height to minimize downtime

2.   Make sure that the new binary is executable.

`chmod 755 dydxprotocold`

1.   Wait for the old binary to stop at the upgrade height (this should happen automatically).
2.   Restart the application using the **new binary from step 1**.

`./dydxprotocold start --p2p.seeds="[seed_node_id]@[seed_node_ip_addr]:26656" --bridge-daemon-eth-rpc-endpoint="<eth rpc endpoint>"`

#### Upgrading to a Patch Version (e.g. v0.0.2)

1.   Download the [binary](https://github.com/dydxprotocol/v4-chain/releases) for the new release.
2.   Make sure that the new binary is executable.

`chmod 755 dydxprotocold`

1.   Stop the current binary (e.g. Ctrl+C)
2.   Restart the application using the new binary from step 1.

`./dydxprotocold start --p2p.seeds="[seed_node_id]@[seed_node_ip_addr]:26656" --bridge-daemon-eth-rpc-endpoint="<eth rpc endpoint>"`

* * *

Rollback
--------

In the case of an unsuccessful chain upgrade, an incorrect `AppHash` might get persisted by Tendermint. To move forward, validators will need to rollback to the previous state so that upon restart, Tendermint can replay the last block to get the correct `AppHash`. **Please note:** validators should never rollback further than the last invalid block. In extreme edge cases, transactions could be reverted / re-applied for the last block and cause issues.

### ⚒️ Cosmovisor Users

Cosmovisor backs up the `data` directory before attempting an upgrade. To restore to a previous version:

1.   Stop the node (e.g. Ctrl+C)
2.   Then, copy the contents of your backup data directory back to `~/.dydxprotocol`

```
rm -rf ~/.dydxprotocol/data
mv ~/.dydxprotocol/data-backup-YYYY-MM-DD ~/.dydxprotocol/data
```

1.   Restart your node.

`cosmovisor run start --p2p.seeds="[seed_node_id]@[seed_node_ip_addr]:26656" --bridge-daemon-eth-rpc-endpoint="<eth rpc endpoint>"`

### 🦾 Manual Users

If you don't have a data backup:

1.   Stop the node (e.g. Ctrl+C)
2.   Rollback the application and Tendermint state by one block height.

`./dydxprotocold rollback`

1.   Restart your node.

`./dydxprotocold start --p2p.seeds="[seed_node_id]@[seed_node_ip_addr]:26656" --bridge-daemon-eth-rpc-endpoint="<eth rpc endpoint>"`
Title: Cosmovisor

URL Source: https://docs.dydx.xyz/nodes/upgrades/cosmovisor

Markdown Content:
`cosmovisor` is a small process manager for Cosmos SDK application binaries that monitors the governance module for incoming chain upgrade proposals. If it sees a proposal that gets approved, `cosmovisor` can automatically download the new binary, stop the current binary, switch from the old binary to the new one, and finally restart the node with the new binary.

We recommend validators to use `cosmovisor` to run their nodes. This will make low-downtime upgrades smoother, as validators don’t have to manually upgrade binaries during the upgrade. Instead, they can pre-install new binaries, and `cosmovisor` will automatically update them based on the onchain software upgrade proposals.

Configuration
-------------

When Cosmovisor activates an upgrade, it does a backup of the entire data directory by default. This backup can take a very long time to process unless the user does aggressive historical-state-pruning using the `pruning`[configuration on the node](https://docs.dydx.xyz/vercel/path1/docs/pages/nodes/running-node/required-node-configs).

As long as you have access to a previous state [snapshot](https://docs.dydx.xyz/vercel/path1/docs/pages/nodes/running-node/snapshots), we recommend setting the environment variable `UNSAFE_SKIP_BACKUP` to `true` which skips the data backup and allows a much faster upgrade. If your node is configured to only keep a small amount of historical state, then you may be able to get away with running the backup quickly.

More information about Cosmovisor settings can be found in the [Cosmovisor documentation](https://docs.cosmos.network/main/build/tooling/cosmovisor).

Installation
------------

### Using go install

To install the latest version of `cosmovisor`, run the following command:

`go install cosmossdk.io/tools/cosmovisor/cmd/cosmovisor@latest`

### Manual Build

You can also install from source by pulling the cosmos-sdk repository and switching to the correct version and building as follows:

```
git clone https://github.com/cosmos/cosmos-sdk.git
cd cosmos-sdk
git checkout cosmovisor/vx.x.x
make cosmovisor
```

This will build Cosmovisor in `/cosmovisor` directory. Afterwards you may want to put it into your machine's PATH like as follows:

`cp cosmovisor/cosmovisor ~/go/bin/cosmovisor`

To check your Cosmovisor version, run

`cosmovisor version`

Directory structure
-------------------

```
.
├── current -> genesis or upgrades/<name>
├── genesis
│   └── bin
│       └── $DAEMON_NAME
└── upgrades
    └── <name>
        ├── bin
        │   └── $DAEMON_NAME
        └── upgrade-info.json
```

Initializing Cosmovisor
-----------------------

1.   Rename binary to `dydxprotocold`

`mv dydxprotocold.<version>-<platform> dydxprotocold`

1.   Set the environment variables

```
export DAEMON_NAME=dydxprotocold
export DAEMON_HOME=<your directory>
```

1.   The directory structure can be initialized with

`cosmovisor init <path to executable>`

*   `DAEMON_HOME` should be set to the **validator’s home directory** since Cosmovisor polls `/data/` for upgrade info.
*   `DAEMON_NAME` should be set to `dydxprotocold`

How to run
----------

`cosmovisor` is simply a thin wrapper around Cosmos applications. Use the following command to start a testnet validator using `cosmovisor` .

`cosmovisor run arg1 arg2 arg3 ...`

All arguments passed to `cosmovisor run` will be passed to the application binary (as a subprocess). `cosmovisor` will return `/dev/stdout` and `/dev/stderr` of the subprocess as its own.

Example:

`cosmovisor run start —log-level info —home /dydxprotocol/chain/.alice`

runs

`dydxprotocold start —log-level info —home /dydxprotocol/chain/.alice`

as its subprocess.
Title: Using Cosmovisor to stage dYdX Chain binary upgrade

URL Source: https://docs.dydx.xyz/nodes/upgrades/using-cosmovisor

Markdown Content:
Prerequisite
------------

1.   Linux (Ubuntu Server 22.04.3 recommended)
2.   8-cpu (ARM or x86_64), 64 GB RAM, 500 GB SSD NVME Storage
3.   Already installed dYdXChain full node

Preparation
-----------

1.   Install Go from [https://go.dev/doc/install](https://go.dev/doc/install) (Version tested is 1.22.1)
2.   Install Cosmovisor, with the following command:

*   `go install cosmossdk.io/tools/cosmovisor/cmd/cosmovisor@latest`

1.   Copy cosmovisor from $HOME/go/bin/ to a directory in your $PATH
2.   Add two environment variables to $HOME/.profile. The data directory is typically $HOME/.dydx-mainnet-1

*   `export DAEMON_NAME=dydxprotocold`
*   `export DAEMON_HOME=<your data directory>`

1.   Log out and log back in.
2.   Initialize Cosmovisor with the following command. The `path to executable` is the the full path to dydxprotocold

*   `cosmovisor init <path to executable>`

1.   Cosmovisor is now ready for use.

Running dydxprotocold under Cosmovisor
--------------------------------------

You have to change the way you currently run dydxprotocold to run under Cosmovisor. This is done simply by specifying “cosmovisor run” in place of the “dydxprotocold” command you used previously. Therefore, if you previously used “dydxprotocold start --p2p.seeds="ade4d8…”, you would change that to “cosmovisor run start --p2p.seeds="ade4d8…”

Staging upgrade
---------------

1.   The Cosmovisor directory structure looks like this:

![Image 1: Upgrade1](https://docs.dydx.xyz/Staging_1.png)

1.   To stage an upgrade, you would create a `name` directory inside the upgrades/ directory. For example, as of 4/1/2024, the current version is v3.0.0 and the next upgrade version is v4.0.0. Therefore you would create a directory called “v4.0.0” and then a bin directory inside it.

![Image 2: Upgrade2](https://docs.dydx.xyz/Staging_2.png)

1.   Now, download the upgraded binary and put it inside the bin directory created previously. It must be named dydxprotocold

2.   Restart dydxprotocold with Cosmovisor. Now, Cosmovisor will automatically halt the current binary at the block activation height and start the upgrade binary.
Title: dYdX Documentation

URL Source: https://docs.dydx.xyz/nodes/upgrades/upgrading-sidecar

Published Time: Tue, 21 Oct 2025 22:01:32 GMT

Markdown Content:
dYdX Documentation

===============

[Skip to content](https://docs.dydx.xyz/nodes/upgrades/upgrading-sidecar#vocs-content)

[![Image 3: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Guide

API

Concepts

Nodes

Running Your Node

[Hardware Requirements](https://docs.dydx.xyz/nodes/running-node/hardware-requirement)[Required Node Configs](https://docs.dydx.xyz/nodes/running-node/required-node-configs)[Setup](https://docs.dydx.xyz/nodes/running-node/setup)[Optimize](https://docs.dydx.xyz/nodes/running-node/optimize)[Running a Validator](https://docs.dydx.xyz/nodes/running-node/running-a-validator)[Snapshots](https://docs.dydx.xyz/nodes/running-node/snapshots)[Peering with Gateway](https://docs.dydx.xyz/nodes/running-node/peering-with-gateway)[Voting](https://docs.dydx.xyz/nodes/running-node/voting)

[Node Streaming](https://docs.dydx.xyz/nodes/full-node-streaming)

Upgrades

[Types of Upgrades](https://docs.dydx.xyz/nodes/upgrades/types-of-upgrades)[Performing Upgrades](https://docs.dydx.xyz/nodes/upgrades/performing-upgrades)[Cosmovisor](https://docs.dydx.xyz/nodes/upgrades/cosmovisor)[Using Cosmovisor to Stage dYdX Chain binary upgrade](https://docs.dydx.xyz/nodes/upgrades/using-cosmovisor)[Upgrading Sidecar](https://docs.dydx.xyz/nodes/upgrades/upgrading-sidecar)

[Network Constants](https://docs.dydx.xyz/nodes/network-constants)[Resources](https://docs.dydx.xyz/nodes/resources)

Policies

Search...

[![Image 4: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

[![Image 5: Logo](https://dydx.exchange/icon.svg)](https://docs.dydx.xyz/)

Menu

Upgrading Sidecar

On this page

Starting in `v5.0.0`, all validating full nodes should be running the [Sidecar](https://docs.dydx.xyz/vercel/path1/docs/pages/nodes/running-node/optimize). Non validating full nodes do not need to run the sidecar.

Follow instructions [here](https://docs.skip.build/connect/validators/faq#how-do-i-upgrade-the-connect-binary) to upgrade the sidecar.

Last updated: 9/19/25, 5:57 AM

[Using Cosmovisor to Stage dYdX Chain binary upgrade Previous shift←](https://docs.dydx.xyz/nodes/upgrades/using-cosmovisor)[Network Constants Next shift→](https://docs.dydx.xyz/nodes/network-constants)
Title: Network Constants

URL Source: https://docs.dydx.xyz/nodes/network-constants

Published Time: Tue, 21 Oct 2025 16:16:01 GMT

Markdown Content:
Guide

API

Concepts

Nodes

Running Your Node

[Hardware Requirements](https://docs.dydx.xyz/nodes/running-node/hardware-requirement)[Required Node Configs](https://docs.dydx.xyz/nodes/running-node/required-node-configs)[Setup](https://docs.dydx.xyz/nodes/running-node/setup)[Optimize](https://docs.dydx.xyz/nodes/running-node/optimize)[Running a Validator](https://docs.dydx.xyz/nodes/running-node/running-a-validator)[Snapshots](https://docs.dydx.xyz/nodes/running-node/snapshots)[Peering with Gateway](https://docs.dydx.xyz/nodes/running-node/peering-with-gateway)[Voting](https://docs.dydx.xyz/nodes/running-node/voting)

[Node Streaming](https://docs.dydx.xyz/nodes/full-node-streaming)

Upgrades

[Network Constants](https://docs.dydx.xyz/nodes/network-constants)[Resources](https://docs.dydx.xyz/nodes/resources)

Policies
Title: Resources

URL Source: https://docs.dydx.xyz/nodes/resources

Markdown Content:
`networks` Repositories
-----------------------

mainnet: [https://github.com/dydxopsdao/networks/tree/main/dydx-mainnet-1](https://github.com/dydxopsdao/networks/tree/main/dydx-mainnet-1)

testnet: [https://github.com/dydxprotocol/v4-testnets/tree/main/dydx-testnet-4](https://github.com/dydxprotocol/v4-testnets/tree/main/dydx-testnet-4)

Upgrades History
----------------

mainnet
| Block Height | Compatible Versions | Comments |
| --- | --- | --- |
| 1 ~ 1,805,000 | [v2.0.1](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv2.0.1) [v1.0.1](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv1.0.1) [v1.0.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv1.0.0) | `v1.0.1` was a rolling upgrade; `v2.0.1` was backported to enable easier syncing from block 1 |
| 1,805,001 ~ 7,147,832 | [v2.0.1](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv2.0.1) [v2.0.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv2.0.0) | `v2.0.0` was an emergency fix |
| 7,147,833 ~ 12,791,712 | [v3.0.2](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv3.0.2) [v3.0.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv3.0.0) | `v3.0.2` allows easier syncing from block 1 |
| 12,791,713 ~ 14,404,200 | [v4.0.5](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv4.0.5) |  |
| 14,404,201 ~ 17,560,000 | [v4.1.2](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv4.1.2) [v4.1.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv4.1.0) | `v4.1.2` adds performance improvements |
| 17,560,001 ~ 21,142,000 | [v5.0.6](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv5.0.6) [v5.0.4](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv5.0.4) [v5.0.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv5.0.0) | `v5.0.4` adds performance improvements `v5.0.6` fixes a chain liveness issue |
| 21,142,001 ~ 22,170,000 | [v5.1.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv5.1.0) |  |
| 22,170,001 ~ 26,785,000 | [v5.2.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv5.2.0) |  |
| 26,785,001 ~ 29,950,000 | [v6.0.4](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv6.0.4) [v6.0.9](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv6.0.9) | `v6.0.9` a Comet Security patch `v6.0.4` Integrates and adds Marketmap functionality, expands transaction sequence number validation to accept timestamp nonces, and introduces individual vault parameters. |
| 29,950,001 ~ 35,602,000 | [v7.0.1](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv7.0.1) | `v7.0.1` * MegaVault * Permissionless / Instant Market Listing * Affiliates Program * Optimistic Execution * Comet Security patch |
| 35,602,001 ~ 48,980,000 | [v8.0.5](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv8.0.5) [v8.0.1](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv8.0.1) | `v8.0.5` Addresses ASA-2025-001 and ASA-2025-002 `v8.0.1` changes in Permissioned Keys, Marketmap Removals |
| 48,980,001 ~ 50,240,951 | [v8.1.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv8.1.0) | `v8.1.0` * Builder Codes * Clob Transaction Batching * Cross Instant Market Listings * IML_5x liquidity tier |
| 50,240,952 ~ 54,450,000 | [v8.2.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv8.2.0) | `v8.2.0` Addresses ISA-2025-005 |
| 54,450,001 ~ 56,530,000 | [v9.0.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv9.0.0) | `v9.0.0` * TWAP Orders * Order Router Revenue Sharing * Proposer Set Reduction |
| 56,530,001 ~ | [v9.1.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv9.1.0) | `v9.1.0` Fixes validator set hash computation to match standard CometBFT |

testnet
| Block Height | Compatible Versions | Comments |
| --- | --- | --- |
| 1 ~ 5,000,000 | [v2.0.1](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv2.0.1) [v2.0.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv2.0.0) [v1.0.1](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv1.0.1) [v1.0.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv1.0.0) | The chain was never upgraded to `v2.0.0` |
| 5,000,001 ~ 6,880,000 | [v3.0.2](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv3.0.2) [v3.0.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv3.0.0) |  |
| 6,880,001 ~ 10,450,000 | [v4.0.5](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv4.0.5) |  |
| 10,450,001 ~ 12,072,000 | [v4.1.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv4.1.0) |  |
| 12,072,001 ~ 16,291,700 | [v5.0.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv5.0.0) |  |
| 16,291,701 ~ 17,707,000 | [v5.1.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv5.1.0) |  |
| 17,707,001 ~ 19,487,300 | [v6.0.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv6.0.0) |  |
| 19,487,301 ~ 20,580,000 | [v6.0.3-rc0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv6.0.3-rc0) |  |
| 20,580,001 ~ 21,670,000 | [v6.0.4-rc2](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv6.0.4-rc2) |  |
| 21,670,001 ~ 23,527,800 | [v7.0.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv7.0.0) |  |
| 23,527,801 ~ 28,235,000 | [v8.0.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv8.0.0) |  |
| 28,235,001 ~ 42,857,848 | [v8.1.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv8.1.0) |  |
| 42,857,849 ~ 46,589,845 | [v8.2.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv8.2.0) |  |
| 46,589,846 ~ 49,045,933 | [v9.0.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv9.0.0) |  |
| 49,045,934 ~ | [v9.1.0](https://github.com/dydxprotocol/v4-chain/releases/tag/protocol%2Fv9.1.0) |  |

Seed Nodes
----------

mainnet
| Team | URI |
| --- | --- |
| Polkachu | `ade4d8bc8cbe014af6ebdf3cb7b1e9ad36f412c0@seeds.polkachu.com:23856` |
| KingNodes | `df1f145848d253800d4e4216e8793158688912f1@seeds.kingnodes.com:23856` |
| Enigma | `6a720a1e5e8be9acf2752b22dc868ea2f95aaaf7@dydx-seeds.enigma-validator.com:1490` |
| Lavender.Five | `20e1000e88125698264454a884812746c2eb4807@seeds.lavenderfive.com:23856` |
| CryptoCrew | `c2c2fcb5e6e4755e06b83b499aff93e97282f8e8@tenderseed.ccvalidators.com:26401` |
| DSRV | `a9cae4047d5c34772442322b10ef5600d8e54900@dydx-mainnet-seednode.allthatnode.com:26656` |
| Luganodes | `802607c6db8148b0c68c8a9ec1a86fd3ba606af6@64.227.38.88:26656` |
| AutoStake | `ebc272824924ea1a27ea3183dd0b9ba713494f83@dydx-mainnet-seed.autostake.com:27366` |

testnet
| Team | URI |
| --- | --- |
| AllThatNode | `19d38bb5cea1378db3e16615e63594dc26119a1a@dydx-testnet4-seednode.allthatnode.com:26656` |
| Crosnest: | `87ee8de5f0f82af6ee6740a30f8844bbe6434413@seed.dydx-testnet.cros-nest.com:26656` |
| CryptoCrew: | `38e5a5ec34c578dc323cbdd9b98330abb448d586@tenderseed.ccvalidators.com:29104` |

Indexer Endpoints
-----------------

See [Endpoints](https://docs.dydx.xyz/interaction/endpoints#indexer).

State Sync Nodes
----------------

mainnet
| Team | State Sync Peers | Region |
| --- | --- | --- |
| Polkachu | `580ec248de1f41d4e50abe132b7838348db55b80@176.9.144.40:23856` | Germany |
| Polkachu | `90b0ee8e73d8237b06356b244ff9854d1991a1f8@65.109.115.228:23856` | Finland |
| Polkachu | `874b5ab53d8f5edae6674ad394f20e2b297cf73f@199.254.199.182:23856` | Japan |
| Polkachu | `e3aa07f6f97fcccdf57b64aa5f4f11761df3852a@15.235.160.15:23856` | Singapore |
| Polkachu | `a879fe2926c2b8f0d86e8e973210c30b8634abb4@15.235.204.159:23856` | Singapore |
| KingNodes | `f94dcfbccb9019584d1790562a020507b050d9ba@51.77.56.23:23856` | EU_West |
| KingNodes | `6bc1068d9a257931083ddc75ad3b1003a46e5b0d@15.235.160.127:23856` | Asia_SE |
| Enigma | `6a720a1e5e8be9acf2752b22dc868ea2f95aaaf7@135.181.183.118:1490` | Finland |
| Enigma | `808b461b4b92f1ad0b507ec4d7af78a67b1ce910@65.108.206.55:1490` | Finland |
| Enigma | `4e7ad7c7a8e8054d2005ea669b9329934882b58c@136.243.35.160:1490` | Germany |
| Enigma | `0e3294d191133ac99f97f38fffc5a98dfbfd9986@148.251.76.7:1490` | Germany |
| Enigma | `dbb678c8cbc19609d9d2aaf97303028135e1376f@5.104.86.93:1490` | Japan |
| AutoStake | `ebc272824924ea1a27ea3183dd0b9ba713494f83@dydx-mainnet-peer.autostake.com:27366` | EU_Poland |

testnet
| Team | State Sync Peers |
| --- | --- |
| Polkachu | `0d17772cbba3b488ad895b17b9a48948e480b1fa@65.109.23.114:23856` |

State Sync Service
------------------

mainnet
| Team | URI |
| --- | --- |
| Enigma | [https://dydx-dao-rpc.enigma-validator.com:443](https://dydx-dao-rpc.enigma-validator.com/) |
| Lavender.Five | [https://services.lavenderfive.com/mainnet/dydx/statesync](https://services.lavenderfive.com/mainnet/dydx/statesync) |
| AutoStake | [https://autostake.com/networks/dydx/#state-sync](https://autostake.com/networks/dydx/#state-sync) |

testnet
| Team | URI |
| --- | --- |
| Lavender.Five | [https://services.lavenderfive.com/testnet/dydx/statesync](https://services.lavenderfive.com/testnet/dydx/statesync) |

Snapshot Service
----------------

mainnet
| Team | URI | Pruning | Index |
| --- | --- | --- | --- |
| Polkachu | `https://polkachu.com/tendermint_snapshots/dydx` | Yes | null |
| KingNodes | `https://snapshots.kingnodes.com/network/dydx` | No | kv |
| Enigma | `https://enigma-validator.com/stake-with-us/dydx#services` | Yes |  |
| Lavender.Five | `https://services.lavenderfive.com/mainnet/dydx/snapshot` | Yes |  |
| AutoStake | `https://autostake.com/networks/dydx/#services` | Yes | null |

testnet
| Team | URI | Pruning | Index |
| --- | --- | --- | --- |
| Polkachu | `https://www.polkachu.com/testnets/dydx/snapshots` | Yes | null |

Live Peer Node Providers
------------------------

mainnet
| Team | URI |
| --- | --- |
| Lavender.Five | `https://services.lavenderfive.com/mainnet/dydx#live-peers` |
| Polkachu | `https://polkachu.com/live_peers/dydx` |

testnet
| Team | URI |
| --- | --- |
| Lavender.Five | `https://services.lavenderfive.com/testnet/dydx#live-peers` |

Address Book Providers
----------------------

mainnet
| Team | URI |
| --- | --- |
| AutoStake | `https://autostake.com/networks/dydx/` |
| Polkachu | `https://polkachu.com/addrbooks/dydx` |
| Lavender.Five | `https://services.lavenderfive.com/mainnet/dydx#latest-addrbook` |

testnet
| Team | URI |
| --- | --- |
| Lavender.Five | `https://services.lavenderfive.com/testnet/dydx#latest-addrbook` |

Full Node Endpoints
-------------------

See [Endpoints](https://docs.dydx.xyz/interaction/endpoints#node).

Archival Node Endpoints
-----------------------

mainnet**RPC**
| Team | URI | Rate limit |
| --- | --- | --- |
| Polkachu | `https://dydx-dao-archive-rpc.polkachu.com:443` | 300 req/m |
| KingNodes | `https://dydx-ops-archive-rpc.kingnodes.com:443` | 50 req/m |
| Enigma | `https://dydx-dao-rpc-archive.enigma-validator.com:443` |  |
**REST**
| Team | URI | Rate limit |
| --- | --- | --- |
| Polkachu | `https://dydx-dao-archive-api.polkachu.com:443` | 300 req/m |
| KingNodes | `https://dydx-ops-archive-rest.kingnodes.com:443` | 50 req/m |
| Enigma | `https://dydx-dao-lcd-archive.enigma-validator.com:443` |  |
**gRPC**
| Team | URI | Rate limit |
| --- | --- | --- |
| Polkachu | `https://dydx-dao-archive-grpc-1.polkachu.com:443` `https://dydx-dao-archive-grpc-2.polkachu.com:443` | 300 req/m |
| KingNodes | `https://dydx-ops-archive-grpc.kingnodes.com:443` | 50 req/m |
| Enigma | `https://dydx-dao-grpc-archive.enigma-validator.com:1492` |  |

testnet
No Archival Nodes.

Other Links
-----------

mainnet
| Name | URI |
| --- | --- |
| dYdX Chain Web Frontend | `https://dydx.trade/` |
| Status Page | `https://status.dydx.trade` |
| Mintscan | `https://www.mintscan.io/dydx` |
| Keplr | `https://wallet.keplr.app/chains/dydx` |
| Validator Metrics | `https://p.ap1.datadoghq.com/sb/610e1836-51dd-11ee-a995-da7ad0900009-78607847ff8632d8a96737ed3437f40c` |
| #validators Discord Channel | `https://discord.com/channels/724804754382782534/1029585380170805379` |
| FE Bug Report Form | `https://www.dydxopsdao.com/feedback` |

testnet
| Name | URI |
| --- | --- |
| Public Testnet Front End | `https://v4.testnet.dydx.exchange` |
| Status Page | `https://status.v4testnet.dydx.exchange` |
| Mintscan | `https://www.mintscan.io/dydx-testnet` |
| Keplr | `https://testnet.keplr.app/chains/dydx-testnet` |
| Validator Metrics | `https://p.datadoghq.com/sb/dc160ddf0-05a98d2dbe2a01d8caa5783eb616f826` |
| Discord Channel (Feedback) | `https://discord.com/channels/724804754382782534/1117897181886677012` |
| Google Form (Feedback) | `https://docs.google.com/forms/d/e/1FAIpQLSezLsWCKvAYDEb7L-2O4wOON1T56xxro9A2Azvl6IxXHP_15Q/viewform` |
