# GeoContext — Developer Guide

## Architecture Overview

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────┐
│  FastAPI App  │────▶│  SQLAlchemy      │────▶│  PostgreSQL  │
│  (uvicorn)    │     │  (async)         │     │  + PostGIS   │
│               │     │  + GeoAlchemy2   │     │              │
│  /api/v1/*    │     │  + asyncpg pool  │     │  port 5433   │
└──────┬───────┘     └──────────────────┘     └─────────────┘
       │
       ├── Admin Panel (sqladmin) at /admin
       ├── Health: /healthz, /readyz
       └── Auth: JWT Bearer token (HS256)
```

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (for PostGIS database)
- `docker-compose` (hyphen variant)

### 1. Clone and Environment

```bash
cp .env.example .env
# Edit .env if needed (defaults work for local dev)
```

### 2. Start the Database

```bash
docker run -d --rm --name geocontext_db \
  -p 5433:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=geocontext \
  postgis/postgis:15-3.4
```

Verify it's ready:
```bash
docker exec geocontext_db pg_isready -U postgres
# /var/run/postgresql:5432 - accepting connections
```

### 3. Run Migrations

```bash
.venv/bin/alembic upgrade head
```

This creates all tables: `boundaries`, `sites`, `restricted_zones`, `reports`, `audit_logs`.

### 4. Load Spatial Data

```bash
PYTHONPATH=. .venv/bin/python -m ingestion.main
```

Expected output:
```
Processing EgyptBoundries.geojson into Boundary...   records_upserted=1
Processing GovernratesBoundries.json into Boundary... records_upserted=27
Processing EgyptSites.geojson into Site...            records_upserted=815
Processing IslamicSites.geojson into Site...          records_upserted=2397
Processing ChristianSites.geojson into Site...        records_upserted=358
Processing ProtectedAreas.geojson into RestrictedZone...  records_upserted=50
Processing Ristracted.geojson into RestrictedZone...     records_upserted=2981
```

Total: ~6,629 records across 7 files.

To re-run idempotently (safe to run multiple times):
```bash
PYTHONPATH=. .venv/bin/python -m ingestion.main
```

### 5. Start the API

```bash
PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify:
```bash
curl -s http://localhost:8000/healthz    # {"status":"ok"}
curl -s http://localhost:8000/readyz     # {"status":"ready"}
```

## Docker Compose (Alternative)

If Docker build is fast enough on your machine:

```bash
# Build images
docker-compose build

# Start everything
docker-compose up -d

# Run ingestion (separate profile)
docker-compose --profile ingestion up
```

The compose stack has 4 services:
| Service | Container | Purpose |
|---------|-----------|---------|
| `db` | `geocontext_db` | PostGIS database (port 5433) |
| `migrate` | `geocontext_migrate` | Runs alembic, exits |
| `api` | `geocontext_api` | FastAPI server (port 8000) |
| `ingestion` | `geocontext_ingestion` | Loads data, exits |

## Auth System

All API endpoints require a JWT Bearer token in the `Authorization` header.

### Development Bypass

For local testing without a real Supabase instance, use `ADMIN_BOOTSTRAP_SECRET` from `.env`:

```bash
# .env: ADMIN_BOOTSTRAP_SECRET="local-dev-bootstrap-secret"
TOKEN="local-dev-bootstrap-secret"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/context?lat=30.0444&lon=31.2357
```

This bypass returns admin-level claims, giving access to both API and admin panel.

### Production Auth

In production, obtain a JWT from the User Service (Supabase, HS256). The token must contain:
- `sub`: user ID
- `role`: `"user"` or `"admin"`
- `exp`: expiration timestamp

Set `SUPABASE_JWT_SECRET` in `.env` to the shared secret.

## API Endpoints

### `GET /healthz`
Liveness probe. Always returns 200 if the server is running.

### `GET /readyz`
Readiness probe. Returns 200 only if DB connection succeeds.

### `GET /api/v1/context?lat={}&lon={}&radius={}`

Primary spatial context endpoint. Logic order:
1. Validates lat (-90..90) and lon (-180..180) before any DB query
2. Checks `ST_Contains` against Egypt boundary → if outside, short-circuits with `in_egypt: false`
3. Governorate lookup via `ST_Contains`
4. Nearby sites via `ST_DWithin` (uses `radius` param, config default, or cap at max)
5. Restricted zone intersection via `ST_Intersects`

**Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `lat` | float | required | Latitude (-90 to 90) |
| `lon` | float | required | Longitude (-180 to 180) |
| `radius` | float | 1000m | Detection radius (capped at 5000m) |

**Response shape:**
```json
{
  "in_egypt": true,
  "governorate": "Cairo",
  "at_site": { "name": "...", "categories": [...], "distance_meters": 22.3, ... },
  "nearby_sites": [ { "name": "...", "distance_meters": 211.4, ... } ],
  "zone_warnings": [ { "subtype": "military", "reason": "..." } ]
}
```

### `GET /api/v1/nearby-sites?lat={}&lon={}&category={}&radius={}`

Category-filterable nearby sites. Same radius rules as `/context`.

### `GET /api/v1/nearby-sites/by-governorate?governorate_name={}&category={}`

Find all sites within a governorate polygon by name.

### `POST /api/v1/reports`

Submit a public safety/data-correction report. Rate-limited to 5/minute/IP. Always created with `status: "pending"`.

**Request body:**
```json
{
  "report_type": "hazard",
  "description": "Broken glass on the path",
  "severity": "medium",
  "lat": 30.0444,
  "lon": 31.2357,
  "related_site_id": null
}
```

### Admin Panel

Access at `http://localhost:8000/admin`. Login uses the JWT token (paste it in the "Password" field).

| View | Model | Notes |
|------|-------|-------|
| SiteAdmin | `sites` | Search by name, filter by category |
| BoundaryAdmin | `boundaries` | Read-only |
| RestrictedZoneAdmin | `restricted_zones` | Filter by subtype/source |
| ReportAdmin | `reports` | Verify/reject reports |
| AuditLogAdmin | `audit_logs` | Read-only |

All admins auto-log changes to `audit_logs` via `on_model_change` / `on_model_delete` hooks.

## Manual Testing

Run the test script:
```bash
bash run_tests.sh
```

### Example `curl` Commands

**1. Inside Egypt (Cairo - Tahrir Square):**
```bash
TOKEN="local-dev-bootstrap-secret"
curl -s "http://localhost:8000/api/v1/context?lat=30.0444&lon=31.2357&radius=2000" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**2. Outside Egypt (short-circuit):**
```bash
curl -s "http://localhost:8000/api/v1/context?lat=48.8566&lon=2.3522" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**3. Filtered nearby sites:**
```bash
curl -s "http://localhost:8000/api/v1/nearby-sites?lat=30.0444&lon=31.2357&radius=500&category=islamic" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**4. Sites by governorate:**
```bash
curl -s "http://localhost:8000/api/v1/nearby-sites/by-governorate?governorate_name=Alexandria&category=christian" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**5. Submit a report:**
```bash
curl -s -X POST "http://localhost:8000/api/v1/reports" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"report_type":"hazard","description":"Broken glass on the path","severity":"medium","lat":30.0444,"lon":31.2357}'
```

**6. Rate limit test (submit 6 reports in quick succession — 6th fails with 429):**
```bash
for i in $(seq 1 6); do
  echo "Request $i:"
  curl -s -X POST "http://localhost:8000/api/v1/reports" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"report_type\":\"hazard\",\"description\":\"test $i\",\"lat\":30.0,\"lon\":31.0}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  status={d.get(\"status\",\"ERROR\")}')"
done
```

## Running Automated Tests

```bash
# Run all tests (requires Docker - spins up throwaway PostGIS)
PYTHONPATH=. .venv/bin/pytest tests/ -v
```

Test infrastructure:
- `testcontainers` spins a fresh `postgis/postgis:15-3.4` container per session
- `conftest.py` overrides `DATABASE_URL` to point at the throwaway DB
- Tests use `httpx.AsyncClient` with `ASGITransport` (no network needed)
- Each test gets an isolated DB session

## Known Issues / Tech Debt

- **`ADMIN_BOOTSTRAP_SECRET` bypass** → `app/core/security.py:16-22` — TODO: remove once auth flow is fully wired
- **`SessionMiddleware` secret hardcoded** → `app/main.py:40` — should be an env var
- **No `source` column on `sites` table** — tracked in schema but not implemented
- **No `detection_radius_m` per site** — config-driven default only
- **Rate limiting only on `/reports`** — `/context` and `/nearby-sites` are not rate-limited
- **No pagination** on list endpoints

## Data Model

```
boundaries (id, osm_type, osm_id, name, name_en, name_ar, level, geometry)
sites     (id, osm_type, osm_id, name, name_en, name_ar, categories[], details, geometry)
restricted_zones (id, osm_type, osm_id, name, subtype, source, reason, geometry)
reports   (id, user_id, report_type, description, severity, related_site_id, status, admin_notes, geometry)
audit_logs (id, admin_identifier, action, target_type, target_id, details, created_at)
```

## Project Structure

```
app/
├── admin/           # sqladmin views & auth backend
│   ├── views.py         # AuditedModelView + 5 admin views
│   └── auth_backend.py  # JWT-based admin auth
├── api/             # FastAPI route handlers
│   ├── context.py       # /api/v1/context
│   ├── sites.py         # /api/v1/nearby-sites
│   ├── reports.py       # /api/v1/reports
│   └── health.py        # (unused, health in main.py)
├── core/            # App configuration & infrastructure
│   ├── config.py        # Pydantic settings
│   ├── security.py      # JWT verification
│   ├── db.py            # SQLAlchemy engine + asyncpg pool
│   ├── exceptions.py    # Exception handlers
│   └── logging.py       # Logging setup
├── models/          # SQLAlchemy ORM models
│   ├── base.py          # Base, TimestampMixin, UUIDMixin
│   ├── boundary.py
│   ├── site.py
│   ├── restricted_zone.py
│   ├── report.py
│   └── audit_log.py
├── schemas/         # Pydantic request/response schemas
│   ├── context.py
│   ├── site.py
│   ├── report.py
│   └── auth.py
├── services/        # Business logic
│   ├── spatial.py      # Core spatial context query logic
│   ├── rate_limit.py   # slowapi limiter instance
│   └── audit.py        # (empty - logging in admin/views.py)
└── main.py          # FastAPI app, lifespan, admin, routers
data/                # GeoJSON source files (7 files)
ingestion/           # Data ingestion pipeline
│   ├── source_map.py   # filename → table mapping
│   ├── normalize.py    # OSM property → model fields
│   ├── upsert.py       # PostgreSQL ON CONFLICT upsert
│   ├── load_geojson.py # GeoJSON file reader
│   └── main.py         # Entrypoint
migrations/          # Alembic migrations
tests/               # pytest + testcontainers
│   ├── conftest.py     # Fixtures (PostGIS container, DB, HTTP client)
│   ├── test_health.py
│   ├── test_ingestion.py
│   └── test_normalize.py
└── Dockerfile, Dockerfile.ingestion, docker-compose.yml
```
