# ConsoleWatch

ConsoleWatch is a local-first web app for Moonraker/Klipper printers. It is being built to record, classify, preserve, and review printer console output and restart/state boundaries that are easy to lose when Klipper, firmware, Moonraker, or an MCU reconnects.

The roadmap in [docs/ROADMAP.md](docs/ROADMAP.md) is the source of truth for scope and progress.

## Current Status

Phase 5 event preservation is in progress. The repo currently contains the roadmap, Docker Compose skeleton, FastAPI backend, React/Vite frontend, SQLite table bootstrap, printer profile CRUD API, a frontend printer management page, Moonraker notification-to-entry ingestion, a bounded recent console page, background watch management for watch-enabled printers, rolling retention pruning, manual diagnostic sessions, and rule-triggered preserved captures.

## Planned Architecture

- Backend: FastAPI, SQLAlchemy, SQLite, Pydantic, service-layer modules, and background Moonraker connection workers.
- Frontend: React, TypeScript, Vite, routing-ready app shell, and timezone-safe display helpers.
- Deployment: Docker Compose with persistent SQLite storage in a Docker volume or bind mount.

## Local Development

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

The frontend expects the API at `/api/v1` by default in Docker, or `http://127.0.0.1:8000/api/v1` during local Vite development if `VITE_API_BASE_URL` is set.

## Docker Compose

```powershell
docker compose up --build
```

Defaults:

- Frontend: `http://localhost:8490`
- Backend API: `http://localhost:8010/api/v1`
- SQLite database in Docker: `/data/consolewatch.db`
- Docker volume: `consolewatch_data`

## Portainer Deployment Notes

Use the included `docker-compose.yml` as the stack file. Keep the `consolewatch_data` volume or replace it with a deliberate bind mount to a stable host path.

Do not remove the volume unless you intend to delete all ConsoleWatch data. The SQLite database, saved sessions, preserved captures, and rolling entries will live there once implemented.

## Backup and Restore

When running with the default named volume, back up the SQLite database from the `consolewatch_data` volume. With a bind mount, back up the host folder mounted to `/data`.

Restore by stopping the stack, replacing `consolewatch.db` in the persistent data location, and starting the stack again.

## Frontend Cache Notes

The nginx config serves `index.html` and route fallbacks with no-cache headers so redeployed UI changes should appear after refresh. If a browser still shows old UI, hard-refresh the page or clear the browser cache.

## Trusted LAN Assumptions

ConsoleWatch is designed as a local-first tool for a trusted LAN. Do not expose it directly to the public internet. Moonraker API keys, when implemented, must remain server-side and must not be bundled into frontend assets.

## Moonraker API Notes

Verified from official Moonraker documentation:

- Websocket connections are required for server-generated events such as gcode responses.
- `notify_gcode_response` forwards Klippy gcode responses over the websocket.
- `notify_klippy_ready`, `notify_klippy_shutdown`, and `notify_klippy_disconnected` report Klippy state boundaries.
- `notify_status_update` reports subscribed Klipper object status updates.
- `printer.objects.subscribe` can subscribe a websocket connection to objects such as `webhooks` and `print_stats`.

ConsoleWatch currently includes a Moonraker websocket client shell and a mock notification ingest endpoint for proof testing. A live printer connection was not available in this environment, so live websocket ingestion remains unverified locally. ConsoleWatch still does not assume full historical console backfill support.

## Rolling Watch

When `CONSOLEWATCH_BACKGROUND_WATCH_ENABLED=true`, the backend starts a rolling watch manager during FastAPI lifespan startup. It scans for printers where both `is_enabled` and `console_watch_enabled` are true, starts one websocket ingestion task per watched printer, records supported Moonraker notifications into `console_entries`, and updates printer connection status fields.

Rolling pruning deletes only rows in `console_entries` older than each watched printer's `retention_hours`. Saved manual-session copy rows and preserved-capture copy rows are separate tables and are not deleted by rolling pruning.

Useful endpoints:

- `GET /api/v1/watch/status`
- `POST /api/v1/watch/prune`

## Manual Sessions

Manual diagnostic sessions intentionally copy newly ingested console entries for the selected printer while a session is active. Copied rows live in `manual_session_entries`, so saved sessions survive rolling pruning of `console_entries`.

Useful endpoints:

- `GET /api/v1/sessions`
- `POST /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}`
- `POST /api/v1/sessions/{session_id}/stop`
- `POST /api/v1/sessions/{session_id}/save`
- `DELETE /api/v1/sessions/{session_id}`

## Preserved Captures

Rule-triggered preservation creates a `preserved_console_captures` row when an error-like console entry or state event matches an explicit trigger rule. ConsoleWatch copies rolling entries from 30 minutes before the trigger through 30 minutes after the trigger into `preserved_console_entries`, marks the trigger entry, and records a `detected_events` row.

If another trigger occurs during an active capture window for the same printer, the existing capture is extended instead of creating a duplicate capture.

Useful endpoints:

- `GET /api/v1/preserved-captures`
- `GET /api/v1/preserved-captures/{capture_id}`

## Validation

Phase 1 local validation:

```powershell
python -m compileall backend\app
pip install -e backend[test]
python -m pytest backend\tests
cd frontend
npm run build
```

Docker Compose validation is expected with:

```powershell
docker compose config
docker compose build
```

On the current development machine, the Docker CLI was not available on PATH, so the Docker build path could not be executed locally.

Phase 2 local validation:

```powershell
pip install -e backend[test]
python -m compileall backend\app
python -m pytest backend\tests
cd frontend
npm run build
```

Phase 3 local validation:

```powershell
python -m compileall backend\app
python -m pytest backend\tests
cd frontend
npm run build
```

Phase 4 local validation:

```powershell
python -m compileall backend\app
python -m pytest backend\tests
cd frontend
npm run build
```

Phase 5 local validation:

```powershell
python -m compileall backend\app
python -m pytest backend\tests
cd frontend
npm run build
```
