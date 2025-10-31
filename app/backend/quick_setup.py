#!/usr/bin/env python3
"""
Quick setup script - creates webhook user in database.
Simpler version that handles imports more gracefully.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir / 'src'))

# Set environment variables
# Try PostgreSQL first (if running in docker-compose), fall back to SQLite
if not os.getenv('DATABASE_URL'):
    # Check if we can connect to PostgreSQL (docker-compose setup)
    try:
        os.environ['DATABASE_URL'] = 'postgresql+asyncpg://dydx_user:dydx_password@localhost:5432/dydx_trading'
    except:
        # Fall back to SQLite
        os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./trading.db'

if not os.getenv('MASTER_ENCRYPTION_KEY'):
    os.environ['MASTER_ENCRYPTION_KEY'] = 'e88c560ed589028a32f711042bd79ec94cd25d0974f8006021f124c50a3e5b09'

if not os.getenv('APP_ENV'):
    os.environ['APP_ENV'] = 'development'


async def main():
    try:
        print("📦 Importing modules...")
        from src.db.database import get_database_manager, init_db
        from src.db.models import User
        from src.core.security import encrypt_sensitive_data
        
        print("✅ Imports successful\n")
        
        # Initialize database
        print("🔧 Initializing database...")
        await init_db()
        print("✅ Database initialized\n")
        
        db_manager = get_database_manager()
        
        # Your webhook credentials
        webhook_uuid = 'a911ece1-2c78-41d8-a235-dca941539af9'
        webhook_secret = '0cf6fd0c3c296ac70a9ce21028bf7136c1b00d5aeed225e529117971d8ad86e8'
        
        # Check if user exists
        print(f"🔍 Checking for existing user with UUID: {webhook_uuid}")
        existing_user = await db_manager.get_user_by_webhook_uuid(webhook_uuid)
        
        if existing_user:
            print(f"✅ User already exists: {existing_user.wallet_address}\n")
            
            # Check if mnemonic is missing
            if not existing_user.encrypted_dydx_testnet_mnemonic:
                print("⚠️  Adding missing testnet mnemonic...")
                test_mnemonic = "test walk nut penalty hip pave soap entry language right filter choice"
                existing_user.encrypted_dydx_testnet_mnemonic = encrypt_sensitive_data(test_mnemonic)
                existing_user.dydx_network_id = 11155111
                await db_manager.update_user(existing_user)
                print("✅ Testnet mnemonic added\n")
            
            print("✅ User is ready for webhook testing!")
            return
        
        print("➕ Creating new user...\n")
        
        # Encrypt credentials
        encrypted_secret = encrypt_sensitive_data(webhook_secret)
        test_mnemonic = "test walk nut penalty hip pave soap entry language right filter choice"
        encrypted_mnemonic = encrypt_sensitive_data(test_mnemonic)
        
        # Create user
        test_user = User(
            wallet_address='0x1234567890123456789012345678901234567890',
            webhook_uuid=webhook_uuid,
            encrypted_webhook_secret=encrypted_secret,
            encrypted_dydx_testnet_mnemonic=encrypted_mnemonic,
            dydx_network_id=11155111
        )
        
        created_user = await db_manager.create_user(test_user)
        
        print("✅ User created successfully!\n")
        print(f"📋 Details:")
        print(f"   Wallet: {created_user.wallet_address}")
        print(f"   Webhook UUID: {created_user.webhook_uuid}")
        print(f"   Network: Testnet (11155111)\n")
        
        print("🚀 Ready to test webhook!\n")
        print("Test command:")
        print(f"curl -X POST http://localhost:8000/api/webhooks/signal/{webhook_uuid} \\")
        print(f'  -H "Content-Type: application/json" \\')
        print(f"  -d '{{")
        print(f'    "secret": "{webhook_secret}",')
        print(f'    "symbol": "BTC-USD",')
        print(f'    "side": "buy",')
        print(f'    "size": 0.01')
        print(f"  }}'\n")
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
