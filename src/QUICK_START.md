# Quick Start Guide - Phase 2 Implementation

## What Was Delivered

You now have **4 complete deliverables** for Phase 2:

### 1. 📋 OpenSpec Proposals (`PHASE2_OPENSPEC_PROPOSALS.md`)
Formal specifications for all 5 Phase 2 tasks with requirements and scenarios.

### 2. 🔌 WebSocket Integration Guide (`WEBSOCKET_INTEGRATION_GUIDE.md`)
Complete code examples for real-time dYdX data with 4 working implementations.

### 3. 📊 PNL Calculation Guide (`PNL_CALCULATION_GUIDE.md`)
Step-by-step implementation for calculating realized/unrealized PNL with database schema.

### 4. ✅ Task 1 Implementation (Verify Test Setup)
- `backend/src/core/network_validator.py` - Network validation class
- `backend/src/api/health.py` - Health check endpoints
- `backend/validate_network_config.py` - Configuration validation script
- `TESTNET_MAINNET_GUIDE.md` - Comprehensive switching guide

---

## Getting Started

### Step 1: Validate Your Configuration

```bash
cd dydx-trading-service/backend
python validate_network_config.py
```

Expected output:
```
✅ All validations passed! Configuration is ready.
```

### Step 2: Check Health Endpoints

```bash
# Start the application
docker-compose up -d

# Check network health
curl http://localhost:8000/health/network

# Check configuration
curl http://localhost:8000/health/config

# Check readiness
curl http://localhost:8000/health/ready
```

### Step 3: Review Documentation

- **For testnet/mainnet switching**: Read `TESTNET_MAINNET_GUIDE.md`
- **For WebSocket implementation**: Read `WEBSOCKET_INTEGRATION_GUIDE.md`
- **For PNL calculations**: Read `PNL_CALCULATION_GUIDE.md`
- **For all proposals**: Read `PHASE2_OPENSPEC_PROPOSALS.md`

---

## Key Files Location

```
dydx-trading-service/
├── PHASE2_OPENSPEC_PROPOSALS.md          ← Start here for task specs
├── WEBSOCKET_INTEGRATION_GUIDE.md        ← WebSocket code examples
├── PNL_CALCULATION_GUIDE.md              ← PNL implementation
├── TESTNET_MAINNET_GUIDE.md              ← Network switching
├── IMPLEMENTATION_SUMMARY.md             ← What was built
├── QUICK_START.md                        ← This file
└── backend/
    ├── src/
    │   ├── core/network_validator.py     ← Network validation
    │   └── api/health.py                 ← Health endpoints
    └── validate_network_config.py        ← Validation script
```

---

## Next Steps

### Immediate (This Week)
1. ✅ Run validation script
2. ✅ Check health endpoints
3. ✅ Review documentation
4. ⏭️ **Integrate NetworkValidator into DydxClient**
5. ⏭️ **Add health check routes to main FastAPI app**

### Short Term (Next 1-2 Weeks)
1. Implement Task 2: WebSocket real-time data
2. Implement Task 3: Trading logic audit
3. Implement Task 4: Advanced position management
4. Implement Task 5: Error handling & resilience

### Medium Term (Next Month)
1. Deploy to staging
2. Test all features
3. Deploy to production
4. Monitor and optimize

---

## Integration Steps

### 1. Add Health Endpoints to Main App

In `backend/src/main.py`:

```python
from src.api import health

# Add health routes
app.include_router(health.router)
```

### 2. Add Network Validation to DydxClient

In `backend/src/bot/dydx_client.py`:

```python
from src.core.network_validator import NetworkValidator

@staticmethod
async def create_client(network_id: Optional[int] = None) -> "DydxClient":
    try:
        settings = get_settings()
        
        # Validate network configuration
        validator = NetworkValidator(
            environment=settings.env,
            network_id=network_id
        )
        config, is_safe = validator.get_network_config()
        
        if not is_safe:
            raise ValueError("Network configuration is unsafe")
        
        # ... rest of client creation
```

### 3. Add Startup Validation

In `backend/src/main.py`:

```python
@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup."""
    from src.core.network_validator import NetworkValidator
    from src.core.config import get_settings
    
    settings = get_settings()
    validator = NetworkValidator(environment=settings.env)
    
    try:
        config, is_safe = validator.get_network_config()
        logger.info(f"Network: {config.network_type.value} ({config.chain_id})")
    except ValueError as e:
        logger.error(f"Network validation failed: {e}")
        raise
```

---

## Testing

### Run Validation Script

```bash
# Development
python backend/validate_network_config.py

# Production
python backend/validate_network_config.py --environment production

# Verbose
python backend/validate_network_config.py --verbose
```

### Test Health Endpoints

```bash
# Network health
curl http://localhost:8000/health/network | jq

# Configuration health
curl http://localhost:8000/health/config | jq

# Readiness (Kubernetes)
curl http://localhost:8000/health/ready | jq

# Liveness (Kubernetes)
curl http://localhost:8000/health/live | jq
```

### Test WebSocket (from WEBSOCKET_INTEGRATION_GUIDE.md)

```python
import asyncio
from src.bot.websocket_manager import WebSocketManager

async def test_websocket():
    manager = WebSocketManager(
        ws_url="wss://indexer.v4testnet.dydx.exchange/v4/ws",
        user_address="dydx1..."
    )
    
    # Register handlers
    await manager.register_handler(
        "v4_subaccounts",
        handle_subaccount_update
    )
    
    # Subscribe and listen
    await manager.subscribe("v4_subaccounts")
    await manager.listen()

asyncio.run(test_websocket())
```

---

## Common Commands

### Validate Configuration
```bash
python backend/validate_network_config.py
```

### Start Application
```bash
docker-compose up -d
```

### Check Logs
```bash
docker-compose logs -f backend
```

### Stop Application
```bash
docker-compose down
```

### Switch to Testnet
```bash
# Update .env
APP_ENV=development
DYDX_V4_PRIVATE_KEY=0x...testnet_key...
DYDX_V4_API_WALLET_ADDRESS=dydx1...testnet_address...

# Validate and restart
python backend/validate_network_config.py
docker-compose restart
```

### Switch to Mainnet
```bash
# Update .env
APP_ENV=production
DYDX_V4_PRIVATE_KEY=0x...mainnet_key...
DYDX_V4_API_WALLET_ADDRESS=dydx1...mainnet_address...

# Validate and restart
python backend/validate_network_config.py --environment production
docker-compose restart
```

---

## Troubleshooting

### "Production environment cannot use testnet"
→ Change APP_ENV to development or use mainnet credentials

### "Network configuration is unsafe"
→ Check environment/network combination in TESTNET_MAINNET_GUIDE.md

### "URLs are invalid"
→ Verify REST and WebSocket URLs match network (testnet/mainnet)

### "dYdX credentials not configured"
→ Add DYDX_V4_PRIVATE_KEY and DYDX_V4_API_WALLET_ADDRESS to .env

### Health endpoints return 503
→ Run validation script to identify issues

---

## Documentation Map

| Document | Purpose | When to Read |
|----------|---------|--------------|
| PHASE2_OPENSPEC_PROPOSALS.md | Task specifications | Planning & design |
| WEBSOCKET_INTEGRATION_GUIDE.md | WebSocket implementation | Building Task 2 |
| PNL_CALCULATION_GUIDE.md | PNL calculations | Building Task 4 |
| TESTNET_MAINNET_GUIDE.md | Network switching | Deployment & operations |
| IMPLEMENTATION_SUMMARY.md | What was built | Overview & reference |
| QUICK_START.md | Getting started | Now! |

---

## Success Criteria

✅ **Task 1 Complete When:**
- [ ] Validation script runs without errors
- [ ] Health endpoints return healthy status
- [ ] NetworkValidator prevents unsafe configurations
- [ ] Documentation is clear and complete
- [ ] All code is tested and working

✅ **Ready for Task 2 When:**
- [ ] Task 1 is integrated into main app
- [ ] Health endpoints are deployed
- [ ] Validation script is in CI/CD pipeline
- [ ] Team understands network configuration

---

## Support & Resources

### dYdX Documentation
- [dYdX v4 Docs](https://dydx.exchange/docs)
- [Indexer API](https://dydx.exchange/docs/indexer)
- [WebSocket API](https://dydx.exchange/docs/websocket)
- [Testnet Faucet](https://faucet.v4testnet.dydx.exchange)

### Code Examples
- WebSocket: `WEBSOCKET_INTEGRATION_GUIDE.md` (4 examples)
- PNL: `PNL_CALCULATION_GUIDE.md` (6 functions)
- Network: `backend/src/core/network_validator.py`
- Health: `backend/src/api/health.py`

### Questions?
- Check TESTNET_MAINNET_GUIDE.md troubleshooting section
- Review code comments in implementation files
- Check health endpoint responses for error details

---

## Summary

**You have everything needed to:**
1. ✅ Understand all 5 Phase 2 tasks
2. ✅ Implement WebSocket real-time data
3. ✅ Calculate PNL correctly
4. ✅ Safely switch between testnet/mainnet
5. ✅ Monitor system health

**Next action**: Run `python backend/validate_network_config.py` and review the health endpoints!
