# ConsoleWatch

ConsoleWatch is a local-first web app for Moonraker/Klipper printers. It is being built to record, classify, preserve, and review printer console output and restart/state boundaries that are easy to lose when Klipper, firmware, Moonraker, or an MCU reconnects.

The roadmap in [docs/ROADMAP.md](docs/ROADMAP.md) is the source of truth for scope and progress.

## Current Status

Phase 1 foundation is in progress. The repo currently contains the roadmap, Docker Compose skeleton, FastAPI backend, React/Vite frontend, SQLite table bootstrap, printer profile CRUD API, and a frontend printer management page. Moonraker ingestion, rolling retention, manual sessions, and preserved captures are planned but not implemented yet.

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

## Moonraker API Limitations

Moonraker websocket notifications and log endpoints have not yet been verified in this project. ConsoleWatch will not assume full historical backfill support unless Phase 2 proves it. The app should remain useful even if it can only record from the time it is connected.

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
