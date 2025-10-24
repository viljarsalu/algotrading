Master Plan: Multi-Tenant dYdX Trading Bot Service

1. Project Vision

To create a secure, reliable, and user-friendly SaaS platform that empowers cryptocurrency traders to automate their strategies on the dYdX v4 exchange. The service will feature a modern Web3 login, a private dashboard for credential management, and a highly secure, two-factor webhook system for executing trades based on TradingView alerts. Each user will have complete privacy with notifications delivered to their personal Telegram channel.

2. System Architecture

The application will run as a multi-container environment managed by Docker Compose, consisting of a web application service and a persistent database.

    web-app Service: A Python FastAPI application responsible for serving the front-end, handling API requests, authenticating users, processing webhooks, and executing trades.

    db Service: A PostgreSQL database that securely stores all user data, credentials, and trade states.

User Interaction Flow:

    Authentication: A user connects their Web3 wallet to the front-end and signs a message to log in.

    Configuration: On their private dashboard, the user inputs their encrypted dYdX and Telegram API credentials. The service displays their unique, two-factor webhook details.

    Execution: A TradingView alert fires, sending a request to the user's unique webhook URL with a secret key in the message body.

    Processing: The web-app verifies both factors, retrieves the user's credentials from the db, and executes the trade on dYdX.

    Notification & Monitoring: A confirmation is sent to the user's private Telegram. A background process monitors the trade's status until it's closed by Take Profit or Stop Loss.

3. Technology Stack

    Backend: Python 3.10+, FastAPI

    Frontend: Vanilla JavaScript, Jinja2 Templates

    Styling: Tailwind CSS

    Database: PostgreSQL

    ORM: SQLModel (or SQLAlchemy)

    Web3: web3.py (for signature verification)

    dYdX Client: dydx-chain-py

    Telegram Client: python-telegram-bot (v20+)

    Containerization: Docker & Docker Compose

4. Project Directory Structure

dydx-trading-service/
├── .env                  # Master secrets (DB connection, encryption key)
├── docker-compose.yml    # Defines web-app and db services
├── tailwind.config.js      # Tailwind CSS configuration
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── package.json          # For Tailwind CSS dependency
    └── src/
        ├── main.py           # FastAPI app entry point
        ├── api/              # API Routers
        │   ├── auth.py       # Web3 login endpoints
        │   ├── user.py       # Dashboard data/credential endpoints
        │   └── webhooks.py   # Secure webhook receiver
        ├── bot/              # Core trading logic
        │   ├── dydx_client.py
        │   ├── telegram_manager.py
        │   ├── risk_manager.py
        │   └── state_manager.py
        ├── core/             # Shared application logic
        │   ├── config.py
        │   └── security.py     # Encryption/decryption functions
        ├── db/               # Database management
        │   ├── database.py
        │   └── models.py     # Database table schemas
        ├── static/           # Compiled frontend assets
        │   ├── css/
        │   │   └── styles.css
        │   └── js/
        │       └── app.js
        └── templates/        # Jinja2 HTML templates
            ├── index.html
            └── dashboard.html

5. Database Schema

Two primary tables will be created in the PostgreSQL database.

    users table:

        wallet_address (Primary Key, Text): The user's public Ethereum address.

        webhook_uuid (Text, Unique): The unique ID for the user's webhook URL.

        encrypted_webhook_secret (Text): The encrypted secret key for the webhook body.

        encrypted_dydx_mnemonic (Text): The user's encrypted dYdX wallet mnemonic.

        encrypted_telegram_token (Text): The user's encrypted Telegram bot token.

        encrypted_telegram_chat_id (Text): The user's encrypted Telegram chat ID.

        created_at (Timestamp): Record creation timestamp.

    positions table:

        id (Primary Key, Integer): Unique ID for the position.

        user_address (Foreign Key to users.wallet_address): Links the position to a user.

        symbol (Text): The trading pair (e.g., "BTC-USD").

        status (Text): e.g., "open", "closed".

        entry_price (Numeric): The price at which the position was opened.

        size (Numeric): The size of the position.

        dydx_order_id (Text): The ID of the entry order on dYdX.

        tp_order_id (Text): The ID of the Take Profit order.

        sl_order_id (Text): The ID of the Stop Loss order.

        opened_at (Timestamp): Position opening timestamp.

6. Phased Development Roadmap

Phase 1: Foundation & Database Setup

    Goal: Create a running containerized application with a database connection.

    Tasks:

        Set up the project directory structure.

        Configure docker-compose.yml to run the web-app and db services.

        Define the database schemas in src/db/models.py.

        Implement the database connection logic in src/db/database.py.

        Create a basic FastAPI app in main.py with a health-check endpoint (/).

Phase 2: Web3 Authentication & User Dashboard

    Goal: Allow users to log in with a wallet and manage their credentials on a secure dashboard.

    Tasks:

        Implement robust encryption/decryption functions in src/core/security.py.

        Build the front-end login page (index.html) and dashboard (dashboard.html) using Jinja2 and Tailwind CSS.

        Create the Web3 authentication API endpoints in src/api/auth.py. Upon user creation, generate and store the webhook_uuid and webhook_secret.

        Create the user API endpoints in src/api/user.py to securely fetch dashboard data and update user credentials.

        Write the Vanilla JS (app.js) to handle wallet connection, authentication flow, and dashboard form submissions.

Phase 3: Core Trading Engine Integration

    Goal: Refactor the trading logic to be stateless and operate on a per-user basis.

    Tasks:

        Modify all functions in src/bot/ to accept user-specific credentials as arguments.

        Adapt the state_manager.py to perform CRUD (Create, Read, Update, Delete) operations on the positions table in the database.

        Thoroughly test the trading engine in isolation by manually passing credentials.

Phase 4: Secure Webhook Implementation

    Goal: Activate the end-to-end trading flow triggered by a secure, two-factor webhook.

    Tasks:

        Implement the webhook router in src/api/webhooks.py.

        The router must perform the two-factor verification: check the webhook_uuid from the URL and the webhook_secret from the request body.

        If verification passes, orchestrate the full trade execution: fetch user credentials, calculate risk, place the trade via dydx_client, save the position to the DB via state_manager, and send a notification via telegram_manager.

Phase 5: Background Position Monitoring

    Goal: Reliably monitor and close open trades for all users automatically.

    Tasks:

        Create a background worker process that starts with the FastAPI application.

        This worker will periodically query the positions table for all "open" trades.

        For each open trade, it will check the order status on dYdX.

        If a TP or SL order is filled, it will update the position's status in the database, cancel the remaining order, and send a final closing notification to the user.

7. Security Protocol

Security is the highest priority for this service.

    Credential Encryption: All user-provided secrets (dYdX mnemonic, Telegram tokens, webhook secret) must be encrypted in the database using a strong algorithm (e.g., AES-256). The master encryption key will be stored securely in the .env file.

    Two-Factor Webhook: All trading signals must be authenticated using both the unique URL and the secret key in the message body.

    No Fund Custody: The architecture is non-custodial. The service only has permission to trade on the user's behalf via the provided keys; it can never withdraw funds.

    Standard Web Security: Implement standard web security practices, including HTTPS, rate limiting on API endpoints, and validation of all incoming data.