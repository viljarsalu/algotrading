#!/usr/bin/env python3
"""
Script to verify and update webhook secret for testing.
"""
import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.db.database import get_database_manager, init_db
from src.db.models import User
from src.core.security import encrypt_sensitive_data, get_encryption_manager


async def verify_and_update_secret():
    """Verify the webhook secret and update if needed."""
    try:
        # Initialize database
        print("Initializing database...")
        await init_db()
        
        db_manager = get_database_manager()
        encryption_manager = get_encryption_manager()
        
        # The webhook UUID from your curl request
        webhook_uuid = '61420327-f983-4c36-b736-6d9aaaa25623'
        # The webhook secret from your curl request
        expected_secret = '8002009ce1ceda78c1e69308c88af2b085109db7e63fb68cc75bfb7dc4bdf129'
        
        # Get the user
        print(f"Looking up user with webhook UUID: {webhook_uuid}")
        user = await db_manager.get_user_by_webhook_uuid(webhook_uuid)
        
        if not user:
            print(f"❌ No user found with webhook UUID: {webhook_uuid}")
            return
        
        print(f"✅ User found: {user.wallet_address}")
        
        # Decrypt and verify the stored secret
        if user.encrypted_webhook_secret:
            try:
                stored_secret = encryption_manager.decrypt(user.encrypted_webhook_secret)
                print(f"\n📋 Stored secret: {stored_secret}")
                print(f"📋 Expected secret: {expected_secret}")
                
                if stored_secret == expected_secret:
                    print("\n✅ Secrets match! Authentication should work.")
                else:
                    print("\n❌ Secrets don't match!")
                    print("\nUpdating the webhook secret...")
                    
                    # Encrypt and update the secret
                    new_encrypted_secret = encrypt_sensitive_data(expected_secret)
                    user.encrypted_webhook_secret = new_encrypted_secret
                    
                    # Update in database
                    updated_user = await db_manager.update_user(user)
                    print(f"✅ Webhook secret updated successfully!")
                    
                    # Verify the update
                    verify_secret = encryption_manager.decrypt(updated_user.encrypted_webhook_secret)
                    if verify_secret == expected_secret:
                        print("✅ Verification successful - secret correctly stored")
                    else:
                        print("❌ Verification failed - something went wrong")
                        
            except Exception as e:
                print(f"❌ Error decrypting/updating secret: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("❌ No webhook secret stored for this user")
            print("\nAdding webhook secret...")
            
            # Encrypt and set the secret
            encrypted_secret = encrypt_sensitive_data(expected_secret)
            user.encrypted_webhook_secret = encrypted_secret
            
            # Update in database
            updated_user = await db_manager.update_user(user)
            print(f"✅ Webhook secret added successfully!")
        
        print(f"\n🔧 You can now test with:")
        print(f"curl -X POST http://localhost:8000/api/webhooks/signal/{webhook_uuid} \\")
        print(f'  -H "Content-Type: application/json" \\')
        print(f"  -d '{{")
        print(f'    "secret": "{expected_secret}",')
        print(f'    "symbol": "BTC-USD",')
        print(f'    "side": "buy",')
        print(f'    "size": 0.001')
        print(f"  }}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(verify_and_update_secret())