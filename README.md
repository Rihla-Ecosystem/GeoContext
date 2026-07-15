# GeoContext Module

The GeoContext module handles all spatial data management, geofencing, and geospatial context processing within the Rihla Ecosystem.

## Environment Variables Configuration

The application is configured using environment variables. To set these up locally, copy the `.env.example` file to `.env` and fill in the required values.

### Required Variables

If these variables are missing, the application will refuse to start (Fail-Fast).

| Variable | Description | Example |
| :--- | :--- | :--- |
| `DATABASE_URL` | The asynchronous connection string to the PostGIS database. Must use the `asyncpg` driver. | `postgresql+asyncpg://user:pass@localhost:5432/db` |
| `JWT_PUBLIC_KEY` | The RSA public key used to cryptographically verify incoming JWT authentication tokens. | `-----BEGIN PUBLIC KEY...` |

### Optional Variables

These variables have sensible defaults built into the code, but can be overridden in your `.env` file or deployment environment.

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `local` | Set to `production` to output logs as structured JSON (for Datadog/ELK). Set to `local` for human-readable colorized terminal output. |
| `JWT_ALGORITHM` | `RS256` | The algorithm used for JWT verification. |
| `BACKEND_CORS_ORIGINS` | `["http://localhost:3000", "http://localhost:8000"]` | A JSON-formatted list of origins permitted to make cross-origin requests to the API. |
| `RATE_LIMIT_GLOBAL` | `100/minute` | The default rate limiting threshold applied via `slowapi`. |
| `DEFAULT_DETECTION_RADIUS`| `50.0` | The default radius (in meters) to use for proximity and point-in-polygon geofencing queries. |

## Running via Docker Compose

The stack is containerized and can be launched using Docker Compose.

```bash
# Start the PostGIS database, run migrations, and start the FastAPI server
docker compose up -d

# Start the heavy spatial data ingestion pipeline (Requires GDAL)
docker compose --profile ingestion up
```
