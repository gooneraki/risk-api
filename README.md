# Risk API

FastAPI-based risk metrics API with Redis pub/sub integration for portfolio management and price tracking.

## Architecture

This service is part of a larger microservices architecture that handles:
- Portfolio management (add/update/delete positions)
- Price caching and updates via Redis pub/sub
- User authentication and management
- Risk metrics calculation

## Tech Stack

- **FastAPI** - Web framework
- **PostgreSQL** - Database
- **Redis** - Pub/sub messaging and caching
- **SQLAlchemy** - ORM
- **yFinance** - Market data
- **JWT** - Authentication

## Setup

### Environment Configuration

Copy `env.example` to `.env` and configure:

```bash
ENV=dev                    # dev (FakeRedis), docker (Redis container), prod (Upstash)
DATABASE_URL=postgresql://user:password@localhost:5432/db
JWT_SECRET_KEY=your-secret-key
CORS_ORIGIN=http://localhost:3000
```

### Docker (Recommended)

```bash
# Start all services
docker-compose up --build

# API available at http://localhost:10000
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start services
powershell -ExecutionPolicy Bypass -File local_start.ps1

# Choose: (L)ocal or (D)ocker
```

## API Endpoints

### Portfolio
- `GET /portfolio` - Get user portfolio
- `POST /portfolio` - Add position
- `PUT /portfolio/{symbol}` - Update position
- `DELETE /portfolio/{symbol}` - Remove position

### Risk & Pricing
- `GET /latest-price/{ticker}` - Get cached price
- `GET /search_ticker` - Search tickers
- `POST /trigger-price-update/{ticker}` - Trigger price fetch

### Authentication
- `POST /register` - Register user
- `POST /login` - Login user
- `GET /me` - Get current user

### System
- `GET /healthz` - Health check
- `GET /redis-info` - Redis connection status

## Redis Integration

The service uses Redis for:
- **Pub/sub messaging** - Ticker update events
- **Price caching** - Latest price storage
- **Multi-environment support**:
  - `ENV=dev` - FakeRedis (no external Redis needed)
  - `ENV=docker` - Redis container
  - `ENV=prod` - Upstash Redis (cloud)

## Development

```bash
# Run locally with hot reload
uvicorn app.main:app --env-file .env --reload --port 10000

# Run tests
pytest

# View logs
docker-compose logs -f risk-api
```

## Environment Variables

Required:
- `ENV` - Environment (dev/docker/prod)
- `DATABASE_URL` - PostgreSQL connection
- `JWT_SECRET_KEY` - JWT signing key
- `CORS_ORIGIN` - CORS allowed origins

Optional (prod only):
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_USER`, `REDIS_PASSWORD` - Redis connection
- `REDIS_DOMAIN`, `REDIS_TLS` - Redis URL configuration