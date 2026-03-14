# URL Shortener API

A FastAPI application for creating and managing shortened URLs, with user authentication, click statistics, and Redis caching.

## Description

The service allows users to create short codes for arbitrary URLs. It supports anonymous and authenticated usage, optional custom aliases, expiration timestamps, per-link click statistics, and a background cleanup task.

Features:
- Create short links (anonymous and authenticated users)
- Optional custom alias per link
- Optional expiration timestamp per link
- Click count and last-used statistics
- Search by original URL
- JWT-based authentication via fastapi-users
- Redis caching for redirect and stats endpoints
- PostgreSQL for persistent storage
- Background task for periodic cleanup of expired and unused links
- Single-page web interface

## Quick Start

### Running with Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/SergeySolovyev/Fast-API_aka_tinyURL.git
cd Fast-API_aka_tinyURL
```

2. Create an environment file:
```bash
cp .env.example .env
# Edit .env and set SECRET_KEY and other required values
```

3. Start the application:
```bash
docker-compose up --build
```

4. Endpoints available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Reference

### Authentication

**Register a user:**
```bash
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "strongpassword"
}
```

**Obtain a JWT token:**
```bash
POST /auth/jwt/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=strongpassword
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### Links

**Create a shortened URL (POST /links/shorten)**

Available to both anonymous and authenticated users.

Without a custom alias:
```bash
POST /links/shorten
Content-Type: application/json

{
  "original_url": "https://www.example.com/very/long/url"
}
```

With a custom alias (requires authentication):
```bash
POST /links/shorten
Content-Type: application/json
Authorization: Bearer <token>

{
  "original_url": "https://www.example.com/article",
  "custom_alias": "my-article"
}
```

With an expiration timestamp:
```bash
POST /links/shorten
Content-Type: application/json

{
  "original_url": "https://example.com/temporary",
  "expires_at": "2026-12-31T23:59:59"
}
```

Response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "short_code": "aBc123",
  "original_url": "https://www.example.com/very/long/url",
  "short_url": "http://localhost:8000/aBc123",
  "custom_alias": null,
  "created_at": "2026-03-07T10:00:00",
  "expires_at": null,
  "click_count": 0
}
```

**Redirect (GET /{short_code})**
```bash
GET /aBc123
```
Returns HTTP 307. The redirect target is cached in Redis for 60 seconds. Click count is incremented on each access.

**Link statistics (GET /links/{short_code}/stats)**
```bash
GET /links/aBc123/stats
```

Response:
```json
{
  "short_code": "aBc123",
  "original_url": "https://www.example.com/article",
  "created_at": "2026-03-07T10:00:00",
  "expires_at": null,
  "click_count": 42,
  "last_used_at": "2026-03-07T15:30:00",
  "category": null
}
```
Cached for 30 seconds.

**Delete a link (DELETE /links/{short_code})**

Requires authentication. Users can only delete their own links.
```bash
DELETE /links/aBc123
Authorization: Bearer <token>
```
Returns HTTP 204 on success.

**Update a link (PUT /links/{short_code})**

Requires authentication. Users can only update their own links.
```bash
PUT /links/aBc123
Authorization: Bearer <token>
Content-Type: application/json

{
  "original_url": "https://new-url.com",
  "expires_at": "2027-01-01T00:00:00"
}
```

**Search by original URL (GET /links/search/by-url)**
```bash
GET /links/search/by-url?original_url=https://www.example.com/article
```
Returns an array of links with the matching original URL.

**List user links (GET /links/user/my-links)**

Requires authentication. Returns all links belonging to the current user.
```bash
GET /links/user/my-links
Authorization: Bearer <token>
```

## Database Schema

### Table: users

| Column          | Type      | Description                    |
|-----------------|-----------|--------------------------------|
| id              | UUID      | Primary key                    |
| email           | String    | Unique email address           |
| hashed_password | String    | Hashed password                |
| registered_at   | Timestamp | Registration timestamp         |
| is_active       | Boolean   | Whether the account is active  |
| is_superuser    | Boolean   | Superuser flag                 |
| is_verified     | Boolean   | Email verification flag        |

### Table: links

| Column       | Type         | Description                           |
|--------------|--------------|---------------------------------------|
| id           | UUID         | Primary key                           |
| short_code   | String(50)   | Unique short code (indexed)           |
| original_url | String(2048) | Target URL                            |
| custom_alias | String(50)   | Optional user-defined alias           |
| user_id      | UUID         | Foreign key to users (NULL for anon)  |
| created_at   | Timestamp    | Creation timestamp                    |
| expires_at   | Timestamp    | Optional expiration timestamp         |
| last_used_at | Timestamp    | Last access timestamp                 |
| click_count  | Integer      | Total redirect count                  |
| category     | String(100)  | Optional category label               |

Indexes: `short_code` (unique), `custom_alias` (unique), `original_url`, `user_id`, composite `(user_id, created_at)`.

## Technology Stack

| Component      | Version / Notes                  |
|----------------|----------------------------------|
| FastAPI        | 0.115+                           |
| SQLAlchemy     | 2.0+ (async)                     |
| PostgreSQL     | 16                               |
| Redis          | 7                                |
| Alembic        | Database migrations              |
| fastapi-users  | Authentication and JWT           |
| Pydantic       | Request/response validation      |
| asyncpg        | Async PostgreSQL driver          |
| Docker Compose | Container orchestration          |

## Environment Variables

| Variable               | Description                   | Default               |
|------------------------|-------------------------------|-----------------------|
| DB_HOST                | PostgreSQL host               | localhost             |
| DB_PORT                | PostgreSQL port               | 5432                  |
| DB_NAME                | Database name                 | url_shortener         |
| DB_USER                | Database user                 | postgres              |
| DB_PASS                | Database password             | postgres              |
| REDIS_HOST             | Redis host                    | localhost             |
| REDIS_PORT             | Redis port                    | 6379                  |
| SECRET_KEY             | JWT signing key               | (required)            |
| BASE_URL               | Application base URL          | http://localhost:8000 |
| UNUSED_LINKS_DAYS      | Cleanup threshold in days     | 90                    |
| CLEANUP_INTERVAL_HOURS | Background cleanup interval   | 24                    |

## Deployment on Render.com

1. Create a PostgreSQL instance (New > PostgreSQL). Copy the internal database URL.
2. Create a Redis instance (New > Key Value Store). Copy the internal Redis URL.
3. Create a Web Service (New > Web Service). Connect the GitHub repository.
   - Runtime: Python 3
   - Build command: `pip install -r requirements.txt`
   - Start command: `sh -c "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port $PORT"`
4. Set the following environment variables in the Web Service:
   - `DATABASE_URL` - PostgreSQL internal URL
   - `REDIS_URL` - Redis internal URL
   - `SECRET_KEY` - a securely generated random string
   - `BASE_URL` - the Render service URL

## Project Structure

```
.
+-- src/
|   +-- auth/
|   |   +-- models.py          User model
|   |   +-- schemas.py         Pydantic schemas
|   |   +-- users.py           fastapi-users configuration
|   +-- links/
|   |   +-- models.py          Link model
|   |   +-- schemas.py         Pydantic schemas
|   |   +-- service.py         Business logic
|   |   +-- router.py          API endpoints
|   +-- redirect/
|   |   +-- router.py          Short-code redirect endpoint
|   +-- config.py              Configuration
|   +-- database.py            Database connection
|   +-- main.py                Application entry point
+-- migrations/
|   +-- versions/
|   |   +-- 001_database_creation.py
|   +-- env.py
+-- tests/
+-- requirements.txt
+-- docker-compose.yml
+-- Dockerfile
+-- alembic.ini
+-- .env.example
+-- .gitignore
+-- README.md
```

## Testing

PostgreSQL and Redis are not required for running tests. Database and cache dependencies are mocked.

Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
```

Run tests:
```bash
pytest
```

Run with coverage (minimum threshold: 90%):
```bash
pytest --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=90
```

HTML coverage report: `htmlcov/index.html`

Load testing with Locust:
```bash
locust -f locustfile.py -H http://localhost:8000
```

Headless mode:
```bash
locust -f locustfile.py --headless --users 20 --spawn-rate 2 -H http://localhost:8000 --run-time 30s
```

## License

MIT License

## Author

Sergey Solovyev
GitHub: https://github.com/SergeySolovyev
