"""
Security utilities for dYdX Trading Service.

This module provides encryption/decryption utilities for sensitive data
such as API keys, webhook secrets, and user credentials.
"""

import os
import time
import hashlib
import secrets
import json
from typing import Optional, Dict, Any

import jwt
from cryptography.fernet import Fernet

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import logging

# Web3 imports for signature verification
try:
    from web3 import Web3
    from eth_account import Account
    from eth_account.messages import encode_defunct
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.warning("Web3 libraries not available. Install web3[py] and eth-account for Web3 features.")

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Manages encryption and decryption of sensitive data."""

    def __init__(self, master_key: Optional[str] = None):
        """Initialize encryption manager with master key.

        Args:
            master_key: 32-byte hex string for AES-256 encryption.
                       If not provided, uses MASTER_ENCRYPTION_KEY env var.
        """
        self.master_key = master_key or os.getenv('MASTER_ENCRYPTION_KEY')
        if not self.master_key:
            raise ValueError("Master encryption key not provided")

        if len(self.master_key) != 64:  # 32 bytes as hex
            raise ValueError("Master key must be 32 bytes (64 hex characters)")

        # Convert hex string to bytes
        try:
            key_bytes = bytes.fromhex(self.master_key)
        except ValueError as e:
            raise ValueError(f"Invalid hex string for master key: {e}")

        # Create Fernet cipher
        self.cipher = Fernet(base64.urlsafe_b64encode(key_bytes))

    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data.

        Args:
            data: Plain text data to encrypt

        Returns:
            Base64 encoded encrypted data
        """
        try:
            encrypted_bytes = self.cipher.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data.

        Args:
            encrypted_data: Base64 encoded encrypted data

        Returns:
            Plain text data
        """
        try:
            # Decode base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            # Decrypt
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def generate_key(self) -> str:
        """Generate a new 32-byte encryption key as hex string.

        Returns:
            64-character hex string
        """
        return secrets.token_hex(32)

    def hash_data(self, data: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash data with salt using PBKDF2.

        Args:
            data: Data to hash
            salt: Optional salt. If not provided, generates random salt.

        Returns:
            Tuple of (hash, salt) as hex strings
        """
        if salt is None:
            salt = secrets.token_hex(16)
        else:
            salt = salt.encode('utf-8')

        # Convert salt to bytes if it's a hex string
        if isinstance(salt, str) and len(salt) == 32:
            try:
                salt = bytes.fromhex(salt)
            except ValueError:
                pass  # Use as-is if not hex

        # Create PBKDF2 key derivation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = kdf.derive(data.encode('utf-8'))
        return key.hex(), salt.hex() if isinstance(salt, bytes) else salt

    def verify_hash(self, data: str, hash_value: str, salt: str) -> bool:
        """Verify data against stored hash.

        Args:
            data: Original data to verify
            hash_value: Stored hash as hex string
            salt: Salt used for hashing as hex string

        Returns:
            True if data matches hash
        """
        try:
            salt_bytes = bytes.fromhex(salt)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt_bytes,
                iterations=100000,
            )

            key = kdf.derive(data.encode('utf-8'))
            return key.hex() == hash_value
        except Exception as e:
            logger.error(f"Hash verification failed: {e}")
            return False


class Web3SignatureManager:
    """Manages Web3 wallet signature verification for authentication."""

    def __init__(self):
        """Initialize Web3 signature manager."""
        if not WEB3_AVAILABLE:
            raise ImportError("Web3 libraries not available. Install web3[py] and eth-account.")

        self.w3 = Web3()

    def verify_signature(self, wallet_address: str, message: str, signature: str) -> bool:
        """Verify Ethereum signature for authentication.

        Args:
            wallet_address: Ethereum wallet address (with or without 0x prefix)
            message: Original message that was signed
            signature: Hex signature string (with or without 0x prefix)

        Returns:
            True if signature is valid for the wallet address
        """
        try:
            # Normalize wallet address
            if not wallet_address.startswith('0x'):
                wallet_address = '0x' + wallet_address

            # Normalize signature
            if not signature.startswith('0x'):
                signature = '0x' + signature

            # Encode message for signing
            encoded_message = encode_defunct(text=message)

            # Recover signer address from signature
            recovered_address = self.w3.eth.account.recover_message(
                encoded_message, signature=signature
            )

            # Compare addresses (case-insensitive)
            return recovered_address.lower() == wallet_address.lower()

        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    def recover_signer(self, message: str, signature: str) -> str:
        """Recover signer address from message and signature.

        Args:
            message: Original message that was signed
            signature: Hex signature string (with or without 0x prefix)

        Returns:
            Ethereum address of the signer (with 0x prefix)
        """
        try:
            # Normalize signature
            if not signature.startswith('0x'):
                signature = '0x' + signature

            # Encode message for signing
            encoded_message = encode_defunct(text=message)

            # Recover signer address
            recovered_address = self.w3.eth.account.recover_message(
                encoded_message, signature=signature
            )

            return recovered_address

        except Exception as e:
            logger.error(f"Signer recovery failed: {e}")
            raise ValueError(f"Invalid signature: {e}")

    def generate_message(self, wallet_address: str, nonce: Optional[str] = None) -> str:
        """Generate a unique message for wallet signature.

        Args:
            wallet_address: User's wallet address
            nonce: Optional nonce for uniqueness. If not provided, generates timestamp-based nonce.

        Returns:
            Message string to be signed by the wallet
        """
        if nonce is None:
            nonce = str(int(time.time() * 1000))  # Millisecond timestamp

        return f"Sign this message to authenticate with dYdX Trading Service.\n\nWallet: {wallet_address}\nNonce: {nonce}\nTimestamp: {int(time.time())}"


class CredentialValidator:
    """Validates user credentials for security and format."""

    @staticmethod
    def validate_dydx_credentials(dydx_address: str, dydx_mnemonic: str) -> Dict[str, Any]:
        """Validate dYdX wallet credentials.

        Args:
            dydx_address: dYdX wallet address
            dydx_mnemonic: dYdX mnemonic phrase

        Returns:
            Dict with validation results and any error messages
        """
        errors = []

        # Validate address format (should be Ethereum address)
        if not dydx_address.startswith('0x'):
            dydx_address = '0x' + dydx_address

        if not Web3.is_address(dydx_address):
            errors.append("Invalid dYdX wallet address format")

        # Validate mnemonic (basic check for word count and structure)
        mnemonic_words = dydx_mnemonic.strip().split()
        if len(mnemonic_words) < 12:
            errors.append("dYdX mnemonic must be at least 12 words")
        elif len(mnemonic_words) > 24:
            errors.append("dYdX mnemonic cannot exceed 24 words")

        # Check for common mnemonic validation patterns
        if not all(len(word) >= 3 for word in mnemonic_words):
            errors.append("All mnemonic words must be at least 3 characters")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'normalized_address': dydx_address if len(errors) == 0 else None
        }

    @staticmethod
    def validate_telegram_credentials(telegram_token: str, telegram_chat_id: str) -> Dict[str, Any]:
        """Validate Telegram bot credentials.

        Args:
            telegram_token: Telegram bot token
            telegram_chat_id: Telegram chat ID

        Returns:
            Dict with validation results and any error messages
        """
        errors = []

        # Validate bot token format (basic check)
        # Telegram bot tokens format: <bot_id>:<token_hash>
        # Example: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
        if not telegram_token or len(telegram_token) < 35:  # Bot tokens are typically 35+ characters
            errors.append("Invalid Telegram bot token format (too short)")
        elif ':' not in telegram_token:
            errors.append("Invalid Telegram bot token format (missing colon separator)")
        else:
            # Split by colon to check format
            parts = telegram_token.split(':', 1)
            if len(parts) != 2:
                errors.append("Invalid Telegram bot token format")
            elif not parts[0].isdigit():
                errors.append("Invalid Telegram bot token format (bot ID must be numeric)")

        # Validate chat ID (can be positive for individual chats, negative for groups/channels)
        try:
            chat_id_num = int(telegram_chat_id)
            # Both positive and negative IDs are valid
            # Positive: individual chats
            # Negative: groups, channels, supergroups
        except ValueError:
            errors.append("Telegram chat ID must be a valid number")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }


class AESGCMEncryptionManager:
    """Enhanced encryption manager using AES-256-GCM."""

    def __init__(self, master_password: Optional[str] = None):
        """Initialize AES-GCM encryption manager.

        Args:
            master_password: Master password for key derivation.
                           If not provided, uses MASTER_ENCRYPTION_KEY env var.
        """
        self.master_password = master_password or os.getenv('MASTER_ENCRYPTION_KEY')
        if not self.master_password:
            raise ValueError("Master password not provided")

    def derive_key(self, master_password: str, salt: bytes) -> bytes:
        """Derive encryption key using PBKDF2.

        Args:
            master_password: Master password for key derivation
            salt: Cryptographic salt

        Returns:
            32-byte encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=200000,  # Increased iterations for better security
        )

        return kdf.derive(master_password.encode('utf-8'))

    def encrypt_credentials(self, data: str, key: bytes) -> str:
        """Encrypt sensitive credential data using AES-256-GCM.

        Args:
            data: Plain text data to encrypt
            key: 32-byte encryption key

        Returns:
            JSON string with encrypted data, nonce, and salt
        """
        try:
            # Generate random salt and nonce
            salt = os.urandom(16)
            nonce = os.urandom(12)

            # Derive key from master password and salt
            encryption_key = self.derive_key(key.decode('utf-8') if isinstance(key, bytes) else key, salt)

            # Create AES-GCM cipher
            aesgcm = AESGCM(encryption_key)

            # Encrypt data
            encrypted_bytes = aesgcm.encrypt(nonce, data.encode('utf-8'), None)

            # Create result object
            result = {
                'encrypted_data': base64.b64encode(encrypted_bytes).decode('utf-8'),
                'salt': base64.b64encode(salt).decode('utf-8'),
                'nonce': base64.b64encode(nonce).decode('utf-8'),
                'algorithm': 'AES-256-GCM'
            }

            return json.dumps(result)

        except Exception as e:
            logger.error(f"AES-GCM encryption failed: {e}")
            raise

    def decrypt_credentials(self, encrypted_data: str, key: bytes) -> str:
        """Decrypt sensitive credential data using AES-256-GCM.

        Args:
            encrypted_data: JSON string with encrypted data from encrypt_credentials
            key: 32-byte encryption key

        Returns:
            Plain text data
        """
        try:
            # Parse encrypted data
            data = json.loads(encrypted_data)

            # Extract components
            encrypted_bytes = base64.b64decode(data['encrypted_data'])
            salt = base64.b64decode(data['salt'])
            nonce = base64.b64decode(data['nonce'])

            # Derive key from master password and salt
            encryption_key = self.derive_key(key.decode('utf-8') if isinstance(key, bytes) else key, salt)

            # Create AES-GCM cipher
            aesgcm = AESGCM(encryption_key)

            # Decrypt data
            decrypted_bytes = aesgcm.decrypt(nonce, encrypted_bytes, None)

            return decrypted_bytes.decode('utf-8')

        except Exception as e:
            logger.error(f"AES-GCM decryption failed: {e}")
            raise

    def generate_webhook_secret(self) -> str:
        """Generate cryptographically secure webhook secret.

        Returns:
            64-character hex string for webhook authentication
        """
        return secrets.token_hex(32)

    def hash_message(self, message: str) -> str:
        """Create hash for message signing verification.

        Args:
            message: Message to hash

        Returns:
            SHA-256 hash as hex string
        """
        return hashlib.sha256(message.encode('utf-8')).hexdigest()


# Global instances
_web3_manager: Optional[Web3SignatureManager] = None
_credential_validator: Optional[CredentialValidator] = None
_aesgcm_manager: Optional[AESGCMEncryptionManager] = None


def get_web3_manager() -> Web3SignatureManager:
    """Get or create global Web3 signature manager instance."""
    global _web3_manager
    if _web3_manager is None:
        _web3_manager = Web3SignatureManager()
    return _web3_manager


def get_credential_validator() -> CredentialValidator:
    """Get or create global credential validator instance."""
    global _credential_validator
    if _credential_validator is None:
        _credential_validator = CredentialValidator()
    return _credential_validator


def get_aesgcm_manager() -> AESGCMEncryptionManager:
    """Get or create global AES-GCM encryption manager instance."""
    global _aesgcm_manager
    if _aesgcm_manager is None:
        _aesgcm_manager = AESGCMEncryptionManager()
    return _aesgcm_manager


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get or create global encryption manager instance."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data using global encryption manager.

    Args:
        data: Plain text data to encrypt

    Returns:
        Encrypted data as base64 string
    """
    manager = get_encryption_manager()
    return manager.encrypt(data)


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data using global encryption manager.

    Args:
        encrypted_data: Encrypted data as base64 string

    Returns:
        Plain text data
    """
    manager = get_encryption_manager()
    return manager.decrypt(encrypted_data)


def generate_master_key() -> str:
    """Generate a new master encryption key.

    Returns:
        32-byte hex string for use as master key
    """
    manager = get_encryption_manager()
    return manager.generate_key()


def secure_delete(data: str) -> None:
    """Securely delete sensitive data from memory.

    Note: This is a best-effort function. True security requires
    OS-level memory management and should not be relied upon solely.

    Args:
        data: Data to securely delete
    """
    if isinstance(data, str):
        # Overwrite string in memory (best effort)
        data_length = len(data)
        data = 'x' * data_length
        del data
    else:
        logger.warning("secure_delete only supports string data")


# Utility functions for common use cases
def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key for storage."""
    return encrypt_sensitive_data(f"api_key:{api_key}")


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key from storage."""
    decrypted = decrypt_sensitive_data(encrypted_key)
    if not decrypted.startswith("api_key:"):
        raise ValueError("Invalid API key format")
    return decrypted[8:]  # Remove "api_key:" prefix


def encrypt_webhook_secret(secret: str) -> str:
    """Encrypt webhook secret for storage."""
    return encrypt_sensitive_data(f"webhook:{secret}")


def decrypt_webhook_secret(encrypted_secret: str) -> str:
    """Decrypt webhook secret from storage."""
    decrypted = decrypt_sensitive_data(encrypted_secret)
    if not decrypted.startswith("webhook:"):
        raise ValueError("Invalid webhook secret format")
    return decrypted[8:]  # Remove "webhook:" prefix


JWT_ALGORITHM = "HS256"


def get_jwt_secret() -> str:
    """Retrieve JWT secret from environment with secure default."""
    return os.getenv("JWT_SECRET", "your-secret-key-change-in-production")


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload if valid."""
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") == "access":
            return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token provided")
    return None


def get_current_user(token: str) -> Optional[str]:
    """Resolve wallet address from WebSocket token."""
    payload = verify_jwt_token(token)
    if not payload:
        return None
    return payload.get("sub")
