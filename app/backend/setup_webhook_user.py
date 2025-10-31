#!/usr/bin/env python3
"""
Setup script to create a user with the specific webhook credentials for testing.

Run with: python3 setup_webhook_user.py
"""
import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set environment variables if not already set
if not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./trading.db'
if not os.getenv('APP_ENV'):
    os.environ['APP_ENV'] = 'development'

from src.db.database import get_database_manager, init_db
from src.db.models import User
from src.core.security import encrypt_sensitive_data


async def setup_webhook_user():
    """Setup user with webhook credentials."""
    try:
        # Initialize database
        print("Initializing database...")
        await init_db()
        print("✅ Database initialized")
        
        db_manager = get_database_manager()
        
        # Your webhook credentials from the curl request
        webhook_uuid = 'a911ece1-2c78-41d8-a235-dca941539af9'
        webhook_secret = '0cf6fd0c3c296ac70a9ce21028bf7136c1b00d5aeed225e529117971d8ad86e8'
        
        # Check if user already exists
        print(f"\nChecking if user exists with webhook UUID: {webhook_uuid}")
        existing_user = await db_manager.get_user_by_webhook_uuid(webhook_uuid)
        
        if existing_user:
            print(f"✅ User already exists: {existing_user.wallet_address}")
            print(f"   Has webhook secret: {existing_user.encrypted_webhook_secret is not None}")
            print(f"   Has testnet mnemonic: {existing_user.encrypted_dydx_testnet_mnemonic is not None}")
            
            # Check if we need to add mnemonic
            if not existing_user.encrypted_dydx_testnet_mnemonic:
                print("\n⚠️  User missing testnet mnemonic. Adding it...")
                test_mnemonic = "test walk nut penalty hip pave soap entry language right filter choice"
                existing_user.encrypted_dydx_testnet_mnemonic = encrypt_sensitive_data(test_mnemonic)
                existing_user.dydx_network_id = 11155111
                await db_manager.update_user(existing_user)
                print("✅ Testnet mnemonic added")
            
            return
        
        print("Creating new user...")
        
        # Encrypt the webhook secret
        encrypted_secret = encrypt_sensitive_data(webhook_secret)
        print("✅ Webhook secret encrypted")
        
        # Create test mnemonic (replace with your actual mnemonic)
        test_mnemonic = "test walk nut penalty hip pave soap entry language right filter choice"
        encrypted_mnemonic = encrypt_sensitive_data(test_mnemonic)
        print("✅ Mnemonic encrypted")
        
        # Create test user
        test_user = User(
            wallet_address='0x1234567890123456789012345678901234567890',
            webhook_uuid=webhook_uuid,
            encrypted_webhook_secret=encrypted_secret,
            encrypted_dydx_testnet_mnemonic=encrypted_mnemonic,
            dydx_network_id=11155111  # Testnet
        )
        
        # Save to database
        created_user = await db_manager.create_user(test_user)
        
        print(f"\n✅ User created successfully!")
        print(f"   Wallet Address: {created_user.wallet_address}")
        print(f"   Webhook UUID: {created_user.webhook_uuid}")
        print(f"   Network: Testnet (11155111)")
        
        print(f"\n🔧 You can now test the webhook with:")
        print(f"curl -X POST http://localhost:8000/api/webhooks/signal/{webhook_uuid} \\")
        print(f'  -H "Content-Type: application/json" \\')
        print(f"  -d '{{")
        print(f'    "secret": "{webhook_secret}",')
        print(f'    "symbol": "BTC-USD",')
        print(f'    "side": "buy",')
        print(f'    "size": 0.01')
        print(f"  }}'\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(setup_webhook_user())
