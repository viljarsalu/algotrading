#!/usr/bin/env python3
import asyncio
import httpx

async def test_faucet():
    async with httpx.AsyncClient() as client:
        try:
            url = "https://faucet.v4testnet.dydx.exchange/faucet/tokens"
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "address": "dydx1h20xxlfzsh4yxhplcveyelgyr0h2dgkagktnhu",
                "subaccount_number": 0,
                "amount": 10000000000  # 10 USDC
            }
            response = await client.post(url, json=data, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(test_faucet())
