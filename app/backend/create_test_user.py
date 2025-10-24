#!/usr/bin/env python3
"""
Script to create a test user with specific webhook credentials for testing.
"""
import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.db.database import get_database_manager, init_db
from src.db.models import User
from src.core.security import encrypt_sensitive_data


async def create_test_user():
    """Create a test user with specific webhook credentials."""
    try:
        # Initialize database
        print("Initializing database...")
        await init_db()
        print("Database initialized successfully")
        
        db_manager = get_database_manager()
        
        # The webhook UUID and secret from your curl request
        webhook_uuid = '61420327-f983-4c36-b736-6d9aaaa25623'
        webhook_secret = '8002009ce1ceda78c1e69308c88af2b085109db7e63fb68cc75bfb7dc4bdf129'
        
        # Check if user already exists
        print(f"Checking if user exists with webhook UUID: {webhook_uuid}")
        existing_user = await db_manager.get_user_by_webhook_uuid(webhook_uuid)
        
        if existing_user:
            print(f"User already exists: {existing_user.wallet_address}")
            print(f"Has webhook secret: {existing_user.encrypted_webhook_secret is not None}")
            return
        
        print("User not found. Creating test user...")
        
        # Encrypt the webhook secret
        encrypted_secret = encrypt_sensitive_data(webhook_secret)
        print(f"Webhook secret encrypted successfully")
        
        # Create test user
        test_user = User(
            wallet_address='0xTest1234567890123456789012345678901234567',
            webhook_uuid=webhook_uuid,
            encrypted_webhook_secret=encrypted_secret
        )
        
        # Save to database
        created_user = await db_manager.create_user(test_user)
        
        print(f"\n✅ Test user created successfully!")
        print(f"Wallet Address: {created_user.wallet_address}")
        print(f"Webhook UUID: {created_user.webhook_uuid}")
        print(f"Has Encrypted Secret: {created_user.encrypted_webhook_secret is not None}")
        print(f"\nYou can now test the webhook with:")
        print(f"curl -X POST http://localhost:8000/api/webhooks/signal/{webhook_uuid} \\")
        print(f'  -H "Content-Type: application/json" \\')
        print(f"  -d '{{")
        print(f'    "secret": "{webhook_secret}",')
        print(f'    "symbol": "BTC-USD",')
        print(f'    "side": "buy",')
        print(f'    "size": 0.001')
        print(f"  }}'\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(create_test_user())