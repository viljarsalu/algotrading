# dYdX Trading Service

A multi-tenant trading platform for dYdX protocol with secure authentication, position monitoring, and webhook integration.

## 🚀 Phase 1: Foundation & Database Setup

This is the complete implementation of Phase 1, providing the foundational architecture for the dYdX Trading Service.

### ✅ What's Included

- **Containerized Architecture**: Docker Compose setup with web application and PostgreSQL database
- **Database Schema**: User and Position models with proper relationships and validation
- **Security Layer**: AES-256 encryption for sensitive data with key management
- **FastAPI Backend**: Production-ready API with health monitoring and CORS support
- **Responsive Frontend**: Tailwind CSS templates for landing page and dashboard
- **Development Tools**: Complete development environment with hot reload

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend asset building)
- Git

## 🛠️ Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd dydx-trading-service
```

### 2. Generate Master Encryption Key

```bash
# Generate a secure 32-byte hex key
python3 -c "import secrets; print('MASTER_ENCRYPTION_KEY=' + secrets.token_hex(32))"
```

### 3. Configure Environment

Edit the `.env` file with your settings:

```bash
cp .env.example .env
# Edit .env with your configuration
```

**Required Settings:**
- `MASTER_ENCRYPTION_KEY`: 64-character hex string (32 bytes)
- Database credentials (can use defaults for development)

### 4. Start the Application

```bash
# Start all services
docker-compose up -d

# Or for development with hot reload
docker-compose -f docker-compose.dev.yml up
```

The application will be available at:
- **Web Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🏗️ Architecture

### Directory Structure

```
dydx-trading-service/
├── .env                          # Environment configuration
├── docker-compose.yml           # Container orchestration
├── tailwind.config.js           # Tailwind CSS configuration
├── init.sql                     # Database initialization
└── backend/
    ├── Dockerfile               # Python application container
    ├── requirements.txt         # Python dependencies
    ├── package.json            # Frontend dependencies
    └── src/
        ├── main.py             # FastAPI application
        ├── core/
        │   ├── config.py       # Application configuration
        │   └── security.py     # Encryption utilities
        ├── db/
        │   ├── database.py     # Database connection
        │   └── models.py       # SQLModel schemas
        ├── static/
        │   ├── css/            # Stylesheets
        │   └── js/             # JavaScript files
        └── templates/          # HTML templates
```

### Services

- **web-app**: FastAPI application with Python 3.11
- **db**: PostgreSQL 14 database with persistent storage

## 🔒 Security Features

- **AES-256 Encryption**: All sensitive data encrypted with master key
- **Environment Variables**: No hardcoded secrets in source code
- **CORS Protection**: Configurable cross-origin resource sharing
- **Input Validation**: Pydantic models with comprehensive validation
- **SQL Injection Prevention**: Parameterized queries with SQLModel

## 📊 Database Schema

### Users Table
- `wallet_address`: Primary key (Ethereum address)
- `webhook_uuid`: Unique identifier for API authentication
- `encrypted_webhook_secret`: Encrypted webhook secret
- `encrypted_dydx_mnemonic`: Encrypted dYdX wallet credentials
- `encrypted_telegram_token`: Encrypted Telegram bot token
- `created_at`: Account creation timestamp

### Positions Table
- `id`: Primary key
- `user_address`: Foreign key to users table
- `symbol`: Trading pair (e.g., BTC-USD)
- `status`: Position status (open, closed, cancelled)
- `entry_price`: Average entry price
- `size`: Position size
- `dydx_order_id`: dYdX order identifier
- `tp_order_id`: Take-profit order ID
- `sl_order_id`: Stop-loss order ID
- `opened_at`: Position opening timestamp

## 🔧 Development

### Local Development Setup

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   npm install
   ```

2. **Run Database**
   ```bash
   docker-compose up db -d
   ```

3. **Run Application**
   ```bash
   cd backend
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Build Frontend Assets**
   ```bash
   npm run dev  # Development build with watch
   npm run prod # Production build
   ```

### Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_database.py -v
```

## 🚦 Health Monitoring

The application includes comprehensive health monitoring:

- **GET /**: Basic health check
- **GET /health/detailed**: Detailed system information
- **GET /ready**: Kubernetes readiness probe
- **GET /live**: Kubernetes liveness probe

## 🔄 API Endpoints

### Health Endpoints
- `GET /` - Application health status
- `GET /health/detailed` - Detailed system metrics
- `GET /ready` - Readiness probe
- `GET /live` - Liveness probe

### Future Endpoints (Phases 2-5)
- `POST /auth/webhook` - Webhook authentication
- `GET /positions` - Position management
- `POST /orders` - Order placement
- `GET /webhooks` - Webhook configuration

## 📝 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MASTER_ENCRYPTION_KEY` | 32-byte hex encryption key | - | Yes |
| `DATABASE_URL` | Database connection string | PostgreSQL | No |
| `APP_ENV` | Environment (development/production) | development | No |
| `APP_HOST` | Server host | 0.0.0.0 | No |
| `APP_PORT` | Server port | 8000 | No |
| `DEBUG` | Debug mode | false | No |
| `CORS_ORIGINS` | Allowed CORS origins | ["http://localhost:3000"] | No |

## 🚀 Deployment

### Production Deployment

1. **Set Production Environment**
   ```bash
   export APP_ENV=production
   export DEBUG=false
   ```

2. **Use Production Docker Image**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Configure Reverse Proxy** (nginx example)
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## 🔮 Future Phases

- **Phase 2**: Web3 Authentication & User Dashboard
- **Phase 3**: Core Trading Engine Integration
- **Phase 4**: Secure Webhook Implementation
- **Phase 5**: Background Position Monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the health endpoints for system status

---

**Phase 1 Status**: ✅ Complete
**Next Phase**: Phase 2 - Web3 Authentication & User Dashboard


## api video
https://www.youtube.com/watch?v=bBYfkYAOL1E&t=192s