# 🗺️ All Available Routes - dYdX Trading Bot

## Summary
- **Total Endpoints**: 47+
- **API Modules**: 9
- **Authentication**: Required for most endpoints (Bearer token)

---

## 🔐 Authentication Routes (`/auth`)

### Login
```
POST /auth/login
```
Web3 wallet authentication with message signing

### Verify
```
POST /auth/verify
```
Verify signed message and get JWT token

### Refresh
```
POST /auth/refresh
```
Refresh JWT token

### Logout
```
POST /auth/logout
```
Logout and invalidate token

### Check
```
GET /auth/check
```
Check if user is authenticated

---

## 👤 User Routes (`/user`)

### Dashboard
```
GET /user/dashboard
```
Get user dashboard data (profile, webhooks, stats)

### Save Credentials
```
POST /user/credentials
```
Save API credentials (encrypted)

### Update Credentials
```
PUT /user/credentials
```
Update existing credentials

### Credentials Status
```
GET /user/credentials/status
```
Get status of configured credentials

### Webhook Info
```
GET /user/webhook-info
```
Get webhook setup instructions

### Regenerate Webhook Secret
```
PUT /user/webhook-secret
```
Generate new webhook secret

### Account Balance
```
GET /user/account-balance
```
Get dYdX account balance and equity

### Profile
```
GET /user/profile
```
Get user profile information

### Update Profile
```
PUT /user/profile
```
Update user profile

---

## 🏥 Health Checks (`/health`)

### General Health
```
GET /health/
```
General application health status

### Network Health
```
GET /health/network
```
Check dYdX network connectivity

### Configuration Health
```
GET /health/config
```
Check application configuration

### Readiness
```
GET /health/ready
```
Kubernetes readiness probe

### Liveness
```
GET /health/live
```
Kubernetes liveness probe

---

## 📊 PNL Routes (`/api/pnl`)

### Position PNL
```
GET /api/pnl/positions/{position_id}
```
Get PNL for specific position

### PNL Summary
```
GET /api/pnl/summary
```
Get overall PNL summary

### PNL History
```
GET /api/pnl/history?limit=50&offset=0&symbol=BTC-USD
```
Get PNL history with pagination

### Performance Metrics
```
GET /api/pnl/performance
```
Get performance metrics (win rate, profit factor, etc)

---

## 📈 Equity Curve Routes (`/api/equity`)

### Equity Curve Dashboard
```
GET /api/equity/dashboard
```
Serve HTML equity curve dashboard

### Equity Curve Data
```
GET /api/equity/curve?days=30
```
Get equity curve data points

### Equity Summary
```
GET /api/equity/summary
```
Get equity summary with metrics

### Milestones
```
GET /api/equity/milestones
```
Get growth milestones

---

## ⚠️ Error Handling Routes (`/api/errors`)

### Error Summary
```
GET /api/errors/summary
```
Get error summary and statistics

### Rate Limit Status
```
GET /api/errors/rate-limit-status
```
Check rate limit status

### Circuit Breakers
```
GET /api/errors/circuit-breakers
```
Get circuit breaker status

### System Health
```
GET /api/errors/system-health
```
Get overall system health

### Error Notifications
```
GET /api/errors/notifications?severity=high&limit=10
```
Get error notifications

### Report Error
```
POST /api/errors/report
```
Report error from client

### Acknowledge Error
```
POST /api/errors/acknowledge/{error_id}
```
Acknowledge error notification

### Degradation Mode
```
GET /api/errors/degradation-mode
```
Check if system is in degradation mode

---

## 🚀 Trading Routes (`/trading`)

### Execute Signal
```
POST /trading/execute-signal
```
Execute trading signal

### TradingView Webhook
```
POST /trading/tradingview-webhook
```
Receive TradingView webhook signals

### Get Positions
```
GET /trading/positions/{user_address}?status=open
```
Get user positions

### Positions Summary
```
GET /trading/positions/{user_address}/summary
```
Get positions summary

### Market Data
```
GET /trading/market/{symbol}
```
Get market data for symbol

### Risk Check
```
POST /trading/risk-check
```
Check risk limits before trading

### Test Telegram
```
POST /trading/test-telegram
```
Test Telegram connection

---

## 🔔 Webhook Routes (`/webhooks`)

### Webhook Signal
```
POST /webhooks/signal/{webhook_uuid}
```
Receive webhook signal

### Test Webhook
```
GET /webhooks/test/{webhook_uuid}
```
Test webhook connection

### Webhook Metrics
```
GET /webhooks/metrics
```
Get webhook system metrics

### Webhook Health
```
GET /webhooks/health
```
Get webhook system health

### Test Signal
```
POST /webhooks/test-signal?format_type=simple
```
Generate test signal

### Circuit Breakers
```
GET /webhooks/circuit-breakers
```
Get circuit breaker status

---

## 🔌 WebSocket Routes

### Dashboard Stream
```
WS /ws/dashboard?token=YOUR_TOKEN
```
Real-time dashboard data stream

### WebSocket Status
```
GET /ws/status/{user_address}
```
Get WebSocket connection status

### Enhanced WebSocket
```
WS /ws/enhanced?token=YOUR_TOKEN
```
Enhanced real-time data stream

---

## 📋 Complete Route List by Method

### GET Endpoints (Read)
```
GET /health/
GET /health/network
GET /health/config
GET /health/ready
GET /health/live
GET /user/dashboard
GET /user/credentials/status
GET /user/webhook-info
GET /user/account-balance
GET /user/profile
GET /api/pnl/positions/{position_id}
GET /api/pnl/summary
GET /api/pnl/history
GET /api/pnl/performance
GET /api/equity/dashboard
GET /api/equity/curve
GET /api/equity/summary
GET /api/equity/milestones
GET /api/errors/summary
GET /api/errors/rate-limit-status
GET /api/errors/circuit-breakers
GET /api/errors/system-health
GET /api/errors/notifications
GET /api/errors/degradation-mode
GET /trading/positions/{user_address}
GET /trading/positions/{user_address}/summary
GET /trading/market/{symbol}
GET /webhooks/metrics
GET /webhooks/health
GET /webhooks/circuit-breakers
GET /ws/status/{user_address}
```

### POST Endpoints (Create/Execute)
```
POST /auth/login
POST /auth/verify
POST /auth/refresh
POST /auth/logout
POST /user/credentials
POST /api/errors/report
POST /api/errors/acknowledge/{error_id}
POST /trading/execute-signal
POST /trading/tradingview-webhook
POST /trading/risk-check
POST /trading/test-telegram
POST /webhooks/signal/{webhook_uuid}
POST /webhooks/test-signal
```

### PUT Endpoints (Update)
```
PUT /user/credentials
PUT /user/webhook-secret
PUT /user/profile
```

### WebSocket Endpoints (Real-time)
```
WS /ws/dashboard
WS /ws/enhanced
```

---

## 🔑 Authentication

Most endpoints require authentication:

```bash
# Include Bearer token in header
Authorization: Bearer YOUR_JWT_TOKEN
```

### Public Endpoints (No Auth Required)
- `GET /health/`
- `GET /health/network`
- `GET /health/config`
- `GET /health/ready`
- `GET /health/live`
- `POST /auth/login`
- `POST /auth/verify`
- `POST /webhooks/signal/{webhook_uuid}`
- `GET /webhooks/test/{webhook_uuid}`
- `POST /webhooks/test-signal`

---

## 📊 Query Parameters

### Pagination
```
?limit=50&offset=0
```

### Filtering
```
?symbol=BTC-USD
?status=open
?severity=high
```

### Time Range
```
?days=30
```

---

## 🚀 Usage Examples

### Get Equity Curve
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/equity/curve?days=30
```

### Get PNL Summary
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/pnl/summary
```

### Get System Health
```bash
curl http://localhost:8000/health/
```

### Execute Trading Signal
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC-USD","side":"BUY","size":1.0}' \
  http://localhost:8000/trading/execute-signal
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/dashboard?token=YOUR_TOKEN');
ws.onmessage = (event) => {
  console.log(JSON.parse(event.data));
};
```

---

## 📱 Response Format

All endpoints return JSON:

```json
{
  "status": "success",
  "data": { /* response data */ },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

Error responses:
```json
{
  "status": "error",
  "detail": "Error message",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## 🔄 Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limited
- `500` - Server Error
- `503` - Service Unavailable

---

## 📝 Notes

- All timestamps are in UTC
- Amounts are in USD
- Prices are in base currency
- All endpoints support CORS
- Rate limiting is applied per user
- WebSocket connections auto-reconnect

---

## 🎯 Common Workflows

### 1. Login Flow
```
POST /auth/login → Get message
POST /auth/verify → Get JWT token
GET /user/dashboard → Get user data
```

### 2. View Portfolio
```
GET /api/equity/dashboard → View equity curve
GET /api/pnl/summary → View PNL
GET /trading/positions/{user_address} → View positions
```

### 3. Execute Trade
```
POST /trading/risk-check → Validate risk
POST /trading/execute-signal → Execute trade
GET /api/pnl/summary → Check results
```

### 4. Monitor System
```
GET /health/ → Check health
GET /api/errors/system-health → Check errors
GET /webhooks/metrics → Check webhooks
```

---

## Summary

✅ **47+ Endpoints** covering:
- Authentication & User Management
- Health Checks & Monitoring
- PNL & Performance Analytics
- Equity Curve Tracking
- Error Handling & Resilience
- Trading Execution
- Webhook Management
- Real-time WebSocket Streaming

**All integrated and ready to use!** 🚀
