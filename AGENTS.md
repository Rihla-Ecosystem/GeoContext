# GeoContext — Context

> Auto-loaded when working here. Keep SHORT.
> Mid-task state: `read CONTEXT.md` (relevant section) first.

## What
FastAPI + PostgreSQL/PostGIS + SQLAlchemy + GeoAlchemy2. Spatial context: Egypt boundary/governorate, nearby tourist sites, restricted zones (~6,629 records). Admin panel (SQLAdmin) with JWT/session auth + audit logs.

## Run / test
- DB (PostGIS on 5433): `docker run -d --rm --name geocontext_db -p 5433:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=geocontext postgis/postgis:15-3.4`
- Migrate: `.venv/bin/alembic upgrade head`
- Ingest: `PYTHONPATH=. .venv/bin/python -m ingestion.main` (idempotent, upsert)
- API: `PYTHONPATH=. .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- Tests: `PYTHONPATH=. .venv/bin/pytest tests/ -v` (spins throwaway PostGIS via testcontainers)

## External contract
- Called by Core-Server + ai-service: `GET /api/v1/context`, `/api/v1/nearby-sites`, `by-governorate`
- Admin CRUD: `/api/v1/sites`, `/boundaries`, `/restricted-zones` (Bearer admin JWT)
- Auth: JWT HS256 (`SUPABASE_JWT_SECRET`); dev bypass `ADMIN_BOOTSTRAP_SECRET`

## Key files
- `app/main.py` (app + admin + routers) · `app/api/context.py` · `app/api/sites.py`
- `app/services/spatial.py` (core queries) · `app/core/security.py` (JWT)
- `ingestion/` (source_map, normalize, upsert) · `data/` (7 GeoJSON files)
- `migrations/versions/*.py` (Alembic)

## Standing rules (enforced reflex)
1. At the end of every task, append a 3–6 line checkpoint to this module's `CONTEXT.md`.
2. At session start, `read` the needed `CONTEXT.md` section before working.
3. Only read sections you need — never dump whole files into replies.
4. Never commit/log `.env` secrets. Match `JWT_ACCESS_SECRET` across services.