# Web3 Authentication and User Dashboard - Change Proposal

## Overview
This change proposal implements Phase 2 of the dYdX Trading Bot Service: enabling secure Web3 wallet authentication and providing users with a private dashboard for credential management.

## Problem Statement
Users need a secure, user-friendly way to authenticate using their Web3 wallets and manage their encrypted credentials for dYdX trading and Telegram notifications. The current foundation lacks user interface and authentication mechanisms.

## Goals
- Implement secure Web3 wallet authentication system
- Create responsive dashboard for credential management
- Enable secure storage and retrieval of user credentials
- Provide seamless user experience for wallet connection and form interactions

## Technical Specifications

### 1. Enhanced Security Module (`src/core/security.py`)

#### Encryption/Decryption Functions
```python
# Key derivation from master password
def derive_key(master_password: str, salt: bytes) -> bytes:
    """Derive encryption key using PBKDF2."""

def encrypt_credentials(data: str, key: bytes) -> str:
    """Encrypt sensitive credential data using AES-256-GCM."""

def decrypt_credentials(encrypted_data: str, key: bytes) -> str:
    """Decrypt sensitive credential data using AES-256-GCM."""

def generate_webhook_secret() -> str:
    """Generate cryptographically secure webhook secret."""

def hash_message(message: str) -> str:
    """Create hash for message signing verification."""
```

#### Web3 Integration Utilities
```python
def verify_signature(wallet_address: str, message: str, signature: str) -> bool:
    """Verify Ethereum signature for authentication."""

def recover_signer(message: str, signature: str) -> str:
    """Recover signer address from message and signature."""
```

### 2. API Architecture

#### Authentication Endpoints (`src/api/auth.py`)
```python
# Web3 Authentication
POST /api/auth/login
# Request: wallet_address, message, signature
# Response: access_token, user_data

POST /api/auth/logout
# Request: access_token
# Response: success confirmation

GET /api/auth/verify
# Request: access_token
# Response: user verification status

# User Management
POST /api/auth/create-user
# Request: wallet_address, signature
# Response: webhook_uuid, webhook_secret (for display only)
```

#### User API Endpoints (`src/api/user.py`)
```python
# Dashboard Data
GET /api/user/dashboard
# Response: user_profile, webhook_info, encrypted_credentials_exist

# Credential Management
POST /api/user/credentials
# Request: dydx_mnemonic, telegram_token, telegram_chat_id
# Response: encryption confirmation

PUT /api/user/credentials
# Request: partial credential updates
# Response: update confirmation

GET /api/user/credentials/status
# Response: which credentials are configured

# Webhook Management
GET /api/user/webhook-info
# Response: webhook_url, instructions for setup

PUT /api/user/webhook-secret
# Response: new webhook secret (requires re-authentication)
```

### 3. Frontend Architecture

#### Login Page (`src/templates/index.html`)
- **Web3 Wallet Connection**: MetaMask/Web3Modal integration
- **Message Signing**: Secure signature request flow
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Error Handling**: User-friendly error messages and retry options
- **Loading States**: Progressive UI updates during authentication

#### Dashboard (`src/templates/dashboard.html`)
- **Navigation**: Clean header with logout functionality
- **Credential Forms**: Secure forms for dYdX and Telegram setup
- **Webhook Information**: Display unique webhook URL and secret
- **Status Indicators**: Visual feedback for configured services
- **Security Warnings**: Clear indicators for missing credentials

#### Styling Strategy
- **Tailwind CSS**: Utility-first CSS framework
- **Responsive Design**: Mobile, tablet, desktop breakpoints
- **Dark Mode**: Professional dark theme for trading interface
- **Accessibility**: WCAG compliant color contrast and navigation
- **Loading States**: Skeleton screens and progress indicators

### 4. JavaScript Implementation (`src/static/js/app.js`)

#### Wallet Connection Module
```javascript
class WalletManager {
    async connectWallet() {
        // MetaMask detection and connection
        // Network validation (Ethereum mainnet)
        // Account switching handling
    }

    async requestSignature(message) {
        // Secure message signing
        // Signature format validation
        // Error handling for user rejection
    }

    async switchNetwork() {
        // Ethereum mainnet enforcement
        // User-friendly network switching
    }
}
```

#### Authentication Flow
```javascript
class AuthManager {
    async login(signature, message) {
        // API call to /api/auth/login
        // Token storage in sessionStorage
        // Redirect to dashboard on success
    }

    async logout() {
        // API call to /api/auth/logout
        // Clear local storage
        // Redirect to login page
    }

    async verifyToken() {
        // Token validation on page load
        // Automatic logout on invalid token
    }
}
```

#### Dashboard Management
```javascript
class DashboardManager {
    async loadDashboard() {
        // Fetch user data and credentials status
        // Update UI with current state
        // Show/hide credential forms
    }

    async saveCredentials(credentials) {
        // Form validation and encryption
        // API call to save credentials
        // Success/error feedback
        // Real-time UI updates
    }

    async updateWebhookSecret() {
        // Re-authentication requirement
        // Generate new webhook secret
        // Update displayed information
    }
}
```

## Implementation Plan

### Phase 2.1: Enhanced Security Foundation
1. **Extend encryption utilities** with Web3 signature verification
2. **Implement key derivation** from master password
3. **Add credential validation** functions
4. **Create webhook secret generation** utilities

### Phase 2.2: API Development
1. **Build authentication endpoints** with proper error handling
2. **Implement user management APIs** with credential encryption
3. **Add rate limiting** and request validation
4. **Create comprehensive API documentation**

### Phase 2.3: Frontend Development
1. **Design responsive login interface** with Web3 integration
2. **Build dashboard layout** with Tailwind CSS
3. **Implement form components** for credential management
4. **Add real-time status indicators** and validation feedback

### Phase 2.4: JavaScript Integration
1. **Implement wallet connection** and network management
2. **Build authentication flow** with signature handling
3. **Create dashboard interactions** for credential management
4. **Add error handling** and user feedback systems

## Dependencies

### Backend Dependencies
- **Web3**: `web3[py]` for signature verification
- **Ethereum**: `eth-account` for address utilities
- **Security**: `cryptography` for enhanced encryption
- **Validation**: `pydantic[email]` for email validation
- **Rate Limiting**: `slowapi` for API protection

### Frontend Dependencies
- **Web3**: `web3modal` for wallet connection
- **Ethereum**: `ethers.js` for blockchain interactions
- **UI Enhancement**: `lucide` for consistent icons
- **Form Handling**: `validator.js` for client-side validation

## Security Considerations

### Authentication Security
- **Signature Verification**: All authentication requires valid Ethereum signatures
- **Message Nonce**: Unique messages prevent replay attacks
- **Token Expiration**: JWT tokens with appropriate expiration times
- **Rate Limiting**: Progressive delays for failed authentication attempts

### Credential Security
- **Client-side Encryption**: Credentials encrypted before transmission
- **Server-side Validation**: Comprehensive validation of all inputs
- **Secure Storage**: Encrypted storage with proper key management
- **Access Logging**: Audit trail for credential access and modifications

### Frontend Security
- **CSP Headers**: Content Security Policy implementation
- **XSS Protection**: Input sanitization and output encoding
- **CSRF Protection**: Token-based request validation
- **Secure Headers**: HTTPS enforcement and security headers

## Testing Strategy

### Unit Tests
- **Security Functions**: Encryption/decryption and signature verification
- **API Endpoints**: Authentication and user management endpoints
- **Frontend Components**: Form validation and user interactions

### Integration Tests
- **Authentication Flow**: Complete Web3 login process
- **Dashboard Operations**: Credential management workflows
- **Error Scenarios**: Network failures and invalid inputs

### End-to-End Tests
- **Wallet Connection**: MetaMask integration testing
- **Full User Journey**: Registration through credential configuration
- **Webhook Integration**: Display and copy functionality

## Success Criteria
- [ ] Web3 wallet connection and authentication functional
- [ ] Dashboard displays user information and webhook details
- [ ] Credential encryption/decryption working correctly
- [ ] Form submissions update user data securely
- [ ] Responsive design works across all device sizes
- [ ] All tests pass with minimum 85% coverage
- [ ] Security audit passes all requirements

## Rollback Plan
- **Database Integrity**: User credential updates are backward compatible
- **Feature Flags**: New endpoints can be disabled without affecting existing functionality
- **Gradual Rollout**: Dashboard features can be introduced incrementally
- **Data Migration**: No data structure changes requiring migration

## Future Dependencies
This phase enables:
- **Phase 3**: Core Trading Engine Integration
- **Phase 4**: Secure Webhook Implementation
- **Phase 5**: Background Position Monitoring

## Open Questions
- **Wallet Support**: Which additional wallets beyond MetaMask to support
- **Network Flexibility**: Multi-network support strategy
- **Session Management**: Token refresh and multi-device handling
- **Analytics**: User behavior tracking requirements

## References
- Master Plan: Phase 2 - Web3 Authentication & User Dashboard
- Project Context: openspec/project.md
- Foundation Proposal: openspec/changes/foundation-database-setup.md