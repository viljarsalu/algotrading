#!/usr/bin/env python3
"""
Request testnet funds from dYdX faucet for a wallet address.
Usage: python request_testnet_funds.py <address>
"""

import asyncio
import sys
from dydx_v4_client.network import TESTNET_FAUCET
from dydx_v4_client.faucet_client import FaucetClient


async def request_funds(address: str):
    """Request testnet funds from the faucet."""
    try:
        print(f"🔄 Requesting testnet funds for: {address}")
        print(f"📡 Faucet endpoint: {TESTNET_FAUCET}")
        
        faucet = FaucetClient(TESTNET_FAUCET)
        result = await faucet.fill(address)
        
        print(f"✅ SUCCESS! Faucet result:")
        print(f"   {result}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python request_testnet_funds.py <dydx_address>")
        print("Example: python request_testnet_funds.py dydx1h20xxlfzsh4yxhplcveyelgyr0h2dgkagktnhu")
        sys.exit(1)
    
    address = sys.argv[1]
    success = asyncio.run(request_funds(address))
    sys.exit(0 if success else 1)
