# GeoContext Module

Spatial context API for the Rihla ecosystem. Given lat/lon, determines governorate, nearby sites, and restricted zones within Egypt.

## Quick Start

```bash
# 1. Set up env
cp .env.example .env

# 2. Start PostGIS database
docker run -d --rm --name geocontext_db -p 5433:5432 \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=geocontext postgis/postgis:15-3.4

# 3. Run migrations
.venv/bin/alembic upgrade head

# 4. Load spatial data
PYTHONPATH=. .venv/bin/python -m ingestion.main

# 5. Start API
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 6. Test it
curl -s "http://localhost:8000/api/v1/context?lat=30.0444&lon=31.2357" \
  -H "Authorization: Bearer local-dev-bootstrap-secret"
```

See [DEVELOPER.md](DEVELOPER.md) for full documentation including:
- Architecture overview
- All API endpoints with examples
- Auth system (JWT HS256)
- Admin panel usage
- Manual and automated testing
- Project structure

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | asyncpg connection string |
| `SUPABASE_JWT_SECRET` | Yes | — | Shared secret for HS256 JWT verification |
| `ADMIN_BOOTSTRAP_SECRET` | No | `change-me-in-production` | Dev bypass for admin panel |
| `ENVIRONMENT` | No | `local` | `local` = colorized logs, `production` = JSON logs |
| `BACKEND_CORS_ORIGINS` | No | `["http://localhost:3000", "http://localhost:8000"]` | Allowed CORS origins |
| `DEFAULT_DETECTION_RADIUS` | No | `1000.0` | Default proximity radius in meters |
| `MAX_DETECTION_RADIUS` | No | `5000.0` | Maximum allowed radius |
| `AT_SITE_RADIUS` | No | `50.0` | Radius to consider user "at" a site |

## Docker Compose

```bash
# Start stack
docker-compose up -d

# Run data ingestion
docker-compose --profile ingestion up
```
