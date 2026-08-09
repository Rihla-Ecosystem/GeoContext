# GeoContext — Handoff

> Read relevant section only. Appends 3–6 lines. Prune Changelog > 25.
> Last updated: 2026-08-07

## Current status
- API UP on 8000 (`.venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000`; setsid nohup). `/healthz`+`/readyz` 200.
- DB `geocontext_db` (PostGIS 5433→5432) UP. Alembic `upgrade head` applied → new tables `location_warnings`, `nearby_services` + site dashboard columns (description, category, governorate, safety_score, risk_level, status, ...).
- Existing data intact: sites 4450, boundaries 29, zones 3364.

## In-progress / next
- (Resume) merged origin/main 7c06693 (dashboard + locations feature).

## Merge notes (this session)
- Remote added `/api/v1/locations` CRUD + analytics/activity/governorates + geojson import/export, new `location_warnings`/`nearby_services` models, and `docker-entrypoint.sh` (waits for db, runs `alembic upgrade head` on boot).
- `app/core/security.py` now also accepts `X-Internal-Api-Key` for service-to-service (returns role admin).
- NOTE: `.venv/bin/uvicorn` + `.venv/bin/pytest` wrappers have stale `/New Volume1/...` shebangs → launch via `.venv/bin/python3 -m uvicorn/-m pytest`.

## Architecture snapshot
- Spatial queries in `app/services/spatial.py`: in-Egypt boundary check (ST_Contains) → governorate → ST_DWithin nearby sites (geodesic meters) → restricted zone intersection.
- `GET /api/v1/context` returns `{in_egypt, governorate, at_site (≤50m), nearby_sites, nearby_services, area_advisories}`.
- Admin = SQLAdmin at `/admin`; audit-logs every create/update/delete (append-only).
- Ingestion: `ingestion/main.py` → 10 files → Boundary/Site/RestrictedZone upserts (500/batch, ON CONFLICT).

## Key facts
- Env: `DATABASE_URL`, `SUPABASE_JWT_SECRET`, `ADMIN_BOOTSTRAP_SECRET`, radius knobs (`DEFAULT/MAX_DETECTION_RADIUS`, `AT_SITE_RADIUS`).
- DB: 4 tables — boundaries, sites, restricted_zones, audit_logs.
- Developer guide: `DEVELOPER.md`.

## Gotchas
- `ADMIN_BOOTSTRAP_SECRET` dev bypass is a known tech-debt (TODO remove).
- Session middleware secret hardcoded in `app/main.py` (should be env).
- `reports` feature REMOVED for good (dropped migration `8f08c5a1be3f`); user incident reports now live in Core-Server (`/api/reports`).

## Changelog
- 2026-08-09: Dead `reports` leftovers removed — Report tab + submit JS from `app/static/index.html`, `POST /api/v1/reports` & rate-limit docs from `DEVELOPER.md`/`run_tests.sh`, inert slowapi limiter (`app/services/rate_limit.py` deleted, `app.main.py`/`config.py`/`.env.example`/`README` cleaned, `slowapi` dropped from `pyproject.toml`). `import app.main` OK. Incident reports now live in Core as decided.
- 2026-08-08: CLOUD DB MILESTONE — branch `feat/cloud-db`. Wired `BACKEND_CORS_ORIGINS` into CORS middleware (`app/main.py`) instead of hardcoded list. Alembic `upgrade head` applied all migrations to Supabase `rihla-geo` (`lzplpwsuyjqctlfefgxn`, pooler aws-1-eu-west-1); PostGIS pre-enabled by Supabase (in `extensions` schema — exclude `spatial_ref_sys` from dumps). Data restored: `sites=4450`, `boundaries=29`, `restricted_zones=3364` (match local). `.env.cloud` (gitignored) holds asyncpg URL. Live validation on :8001: /readyz ready, /nearby-sites, /context, /restricted-zones all return real spatial results. Commit `37c2f33`.
- 2026-08-07: Created `AGENTS.md` + `CONTEXT.md`. Not started this session.
- 2026-08-07: Merged origin/main + alembic upgrade (new tables). Tests 2/2. E2E: `/api/v1/context`, `/api/v1/locations` (new, auth), internal-key service auth all OK.
- 2026-08-07: Sensitive-area feature: added `ZoneGuidance` schema + `nearby_zone_guidance` on ContextResponse; §6 ST_DWithin(geography) proximity query vs `restricted_zones` (limit 5, returns only zone_type+distance). Verified restart (port 8000, no --reload so must fuser -k after edits) → curl `/api/v1/context` with internal key returns guidance near Cairo, `[]` for far point. Note: pre-existing uvicorn held 8000 with stale code — kill by port before testing.