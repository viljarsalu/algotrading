# Testnet/Mainnet Switching Guide

## Overview

This guide explains how to safely switch between dYdX testnet and mainnet environments. The application includes built-in safety checks to prevent accidental mainnet trades during development.

## Network Configuration

### Testnet (Development/Testing)
- **Network ID**: 11155111 (Sepolia)
- **Chain ID**: dydx-testnet-1
- **REST URL**: https://indexer.v4testnet.dydx.exchange
- **WebSocket URL**: wss://indexer.v4testnet.dydx.exchange/v4/ws
- **Purpose**: Safe testing environment with test tokens
- **Trades**: Execute on testnet, no real value
- **Faucet**: Available for test tokens

### Mainnet (Production)
- **Network ID**: 1
- **Chain ID**: dydx-mainnet-1
- **REST URL**: https://indexer.dydx.trade/v4
- **WebSocket URL**: wss://indexer.dydx.trade/v4/ws
- **Purpose**: Production environment with real value
- **Trades**: Execute on mainnet with real funds
- **Faucet**: N/A (requires real funds)

## Automatic Network Selection

The application automatically selects the correct network based on the `APP_ENV` environment variable:

```bash
# Development/Testing → Testnet
APP_ENV=development    # Uses testnet
APP_ENV=testing        # Uses testnet

# Staging/Production → Mainnet
APP_ENV=staging        # Uses testnet (configurable)
APP_ENV=production     # Uses mainnet (REQUIRED)
```

## Environment Configuration

### Development Environment (.env)

```bash
# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# dYdX Configuration
DYDX_V4_PRIVATE_KEY=0x...your_testnet_private_key...
DYDX_V4_API_WALLET_ADDRESS=dydx1...your_testnet_address...

# Database
DATABASE_URL=sqlite+aiosqlite:///./dydx_trading.db

# Security
MASTER_ENCRYPTION_KEY=...64_hex_characters...
```

### Production Environment (.env.production)

```bash
# Application
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# dYdX Configuration (MAINNET)
DYDX_V4_PRIVATE_KEY=0x...your_mainnet_private_key...
DYDX_V4_API_WALLET_ADDRESS=dydx1...your_mainnet_address...

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dydx_trading

# Security
MASTER_ENCRYPTION_KEY=...64_hex_characters...
```

## Safety Checks

### Automatic Validation

The application performs automatic validation at startup:

1. **Environment Check**: Verifies APP_ENV is valid
2. **Network Selection**: Determines testnet/mainnet based on environment
3. **Configuration Validation**: Ensures all required settings are present
4. **Safety Validation**: Prevents unsafe environment/network combinations

### Safety Rules

```
Development/Testing Environment:
  ✅ Can use testnet (default)
  ⚠️  Can use mainnet (with warning)

Staging Environment:
  ✅ Can use testnet (with warning)
  ✅ Can use mainnet (recommended)

Production Environment:
  ✅ MUST use mainnet
  ❌ CANNOT use testnet (will fail)
```

## Validation Script

Run the validation script before deployment:

```bash
# Validate current configuration
python backend/validate_network_config.py

# Validate for specific environment
python backend/validate_network_config.py --environment production

# Verbose output
python backend/validate_network_config.py --verbose
```

**Output Example:**
```
======================================================================
  dYdX Network Configuration Validator
======================================================================

▶ Environment Variables
----------------------------------------------------------------------
  ✅ DYDX_V4_PRIVATE_KEY: 0x...****...
  ✅ DYDX_V4_API_WALLET_ADDRESS: dydx1...****...
  ✅ MASTER_ENCRYPTION_KEY: ****...****

▶ Network Configuration
----------------------------------------------------------------------
  ✅ Environment: development
  ✅ Network Type: TESTNET
  ✅ Network ID: 11155111
  ✅ Chain ID: dydx-testnet-1
  ✅ REST URL: https://indexer.v4testnet.dydx.exchange
  ✅ WebSocket URL: wss://indexer.v4testnet.dydx.exchange/v4/ws
  ✅ URLs are valid and consistent
  ✅ Configuration is safe

▶ Application Configuration
----------------------------------------------------------------------
  ✅ Environment: development
  ✅ Debug Mode: True
  ✅ Log Level: DEBUG
  ✅ Database: Configured
  ✅ Master Encryption Key: Configured
  ✅ dYdX v4 Credentials: Configured

▶ Configuration Issues
----------------------------------------------------------------------
  ✅ No configuration issues found

======================================================================
Validation Result
======================================================================
  ✅ Environment Variables: PASSED
  ✅ Network Configuration: PASSED
  ✅ Application Configuration: PASSED
  ✅ Configuration Issues: PASSED

  ✅ All validations passed! Configuration is ready.
```

## Health Check Endpoints

### Network Health Check

```bash
curl http://localhost:8000/health/network
```

**Response:**
```json
{
  "status": "healthy",
  "network_type": "testnet",
  "network_id": 11155111,
  "chain_id": "dydx-testnet-1",
  "indexer_rest_url": "https://indexer.v4testnet.dydx.exchange",
  "indexer_ws_url": "wss://indexer.v4testnet.dydx.exchange/v4/ws",
  "is_production": false,
  "environment": "development",
  "is_safe": true,
  "warnings": [],
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Configuration Health Check

```bash
curl http://localhost:8000/health/config
```

**Response:**
```json
{
  "status": "healthy",
  "environment": "development",
  "debug": true,
  "database_configured": true,
  "security_configured": true,
  "dydx_configured": true,
  "issues": [],
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Readiness Check (Kubernetes)

```bash
curl http://localhost:8000/health/ready
```

**Response:**
```json
{
  "ready": true,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Getting Testnet Funds

### Step 1: Create Testnet Wallet

```bash
# Using dYdX CLI or web wallet
# Get your testnet address (starts with dydx1...)
```

### Step 2: Get Test Tokens

Visit the dYdX testnet faucet:
- **URL**: https://faucet.v4testnet.dydx.exchange
- **Steps**:
  1. Enter your testnet wallet address
  2. Select token amount
  3. Claim tokens
  4. Wait for confirmation (usually 1-2 minutes)

### Step 3: Verify Funds

```bash
# Check balance via API
curl https://indexer.v4testnet.dydx.exchange/v4/accounts/{your_address}
```

## Switching Between Networks

### From Testnet to Mainnet

1. **Backup testnet configuration**
   ```bash
   cp .env .env.testnet.backup
   ```

2. **Update environment variables**
   ```bash
   APP_ENV=production
   DYDX_V4_PRIVATE_KEY=0x...mainnet_key...
   DYDX_V4_API_WALLET_ADDRESS=dydx1...mainnet_address...
   ```

3. **Validate configuration**
   ```bash
   python backend/validate_network_config.py --environment production
   ```

4. **Check health endpoints**
   ```bash
   curl http://localhost:8000/health/network
   ```

5. **Deploy**
   ```bash
   docker-compose up -d
   ```

### From Mainnet to Testnet

1. **Restore testnet configuration**
   ```bash
   cp .env.testnet.backup .env
   ```

2. **Validate configuration**
   ```bash
   python backend/validate_network_config.py --environment development
   ```

3. **Redeploy**
   ```bash
   docker-compose restart
   ```

## Troubleshooting

### Issue: "Production environment cannot use testnet"

**Cause**: APP_ENV=production but using testnet credentials

**Solution**:
```bash
# Either switch to testnet environment
APP_ENV=development

# Or use mainnet credentials
DYDX_V4_PRIVATE_KEY=0x...mainnet_key...
```

### Issue: "Network configuration is unsafe"

**Cause**: Environment/network combination is not allowed

**Solution**: Check the safety rules above and adjust configuration

### Issue: "URLs are invalid"

**Cause**: Incorrect REST or WebSocket URLs

**Solution**: Verify URLs match the network:
- Testnet: Contains "testnet" in URL
- Mainnet: Does NOT contain "testnet" in URL

### Issue: "dYdX credentials not configured"

**Cause**: Missing DYDX_V4_PRIVATE_KEY or DYDX_V4_API_WALLET_ADDRESS

**Solution**: Add credentials to .env file

### Issue: "Master encryption key not configured"

**Cause**: Missing MASTER_ENCRYPTION_KEY

**Solution**: Generate and add to .env:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Best Practices

1. **Always validate before deployment**
   ```bash
   python backend/validate_network_config.py
   ```

2. **Use different credentials for testnet/mainnet**
   - Never reuse mainnet credentials for testnet
   - Keep mainnet credentials secure

3. **Test on testnet first**
   - Develop and test on testnet
   - Validate behavior before mainnet deployment

4. **Monitor health checks**
   - Regularly check `/health/network` endpoint
   - Set up alerts for unhealthy status

5. **Document environment changes**
   - Keep track of when you switch networks
   - Document any configuration changes

6. **Use environment-specific files**
   - `.env` for development
   - `.env.production` for production
   - Never commit credentials to git

## Security Considerations

### Private Key Management

- **Never commit private keys to git**
- **Use environment variables or secrets manager**
- **Rotate keys regularly**
- **Use different keys for testnet/mainnet**

### Encryption Key Management

- **Generate strong 64-character hex keys**
- **Store securely (AWS Secrets Manager, HashiCorp Vault, etc.)**
- **Rotate periodically**
- **Never share encryption keys**

### Network Isolation

- **Use VPN for production deployments**
- **Restrict API access to authorized IPs**
- **Use HTTPS/WSS in production**
- **Enable rate limiting**

## Monitoring

### Key Metrics to Monitor

1. **Network connectivity**: Check `/health/network` regularly
2. **Configuration status**: Monitor `/health/config`
3. **Error rates**: Track failed API calls
4. **Transaction success rate**: Monitor order execution

### Alerts to Set Up

1. Network health check fails
2. Configuration issues detected
3. High error rate (>5%)
4. Mainnet trades detected in non-production

## Additional Resources

- [dYdX v4 Documentation](https://dydx.exchange/docs)
- [dYdX Testnet Faucet](https://faucet.v4testnet.dydx.exchange)
- [dYdX Indexer API](https://dydx.exchange/docs/indexer)
- [dYdX Trading Guide](https://dydx.exchange/docs/trading)
