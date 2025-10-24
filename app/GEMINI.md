# Project Overview

This project is a multi-tenant trading platform for the dYdX protocol. It provides a secure and robust system for users to automate their trading strategies through webhook integration. The backend is built with Python and FastAPI, utilizing a PostgreSQL database for data persistence. The entire application is containerized using Docker for easy deployment and scalability.

## Key Technologies

*   **Backend:** Python, FastAPI
*   **Database:** PostgreSQL
*   **Containerization:** Docker, Docker Compose
*   **Frontend:** HTML, Tailwind CSS, JavaScript
*   **Security:** AES-256 encryption for sensitive data

## Architecture

The application follows a microservices-oriented architecture, with the main components being:

*   **`web-app`:** The FastAPI application that handles API requests, user authentication, and webhook processing.
*   **`db`:** A PostgreSQL database that stores user data, trading positions, and other application-related information.
*   **Position Monitoring Worker:** A background worker that monitors active trading positions and executes risk management strategies.

# Building and Running

## Prerequisites

*   Docker and Docker Compose
*   Python 3.11+ (for local development)
*   Node.js 18+ (for frontend asset building)
*   Git

## Quick Start

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd dydx-trading-service
    ```

2.  **Configure the environment:**
    *   Copy the `.env.example` file to `.env`.
    *   Generate a master encryption key and update the `MASTER_ENCRYPTION_KEY` variable in the `.env` file.
    *   Update the database credentials and other configuration variables as needed.

3.  **Start the application:**
    ```bash
    docker-compose up -d
    ```

The application will be available at `http://localhost:8000`.

# Development Conventions

## Local Development

1.  **Install dependencies:**
    ```bash
    cd backend
    pip install -r requirements.txt
    npm install
    ```

2.  **Run the database:**
    ```bash
    docker-compose up db -d
    ```

3.  **Run the application:**
    ```bash
    cd backend
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
    ```

4.  **Build frontend assets:**
    ```bash
    npm run dev
    ```

## Testing

To run the test suite, use the following command:

```bash
pytest tests/
```

## API Documentation

The API documentation is available at `http://localhost:8000/docs` when the application is running.
