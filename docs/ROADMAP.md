# ConsoleWatch Roadmap

## Project Overview

ConsoleWatch is a local-first web app for Moonraker/Klipper printers. It continuously records, classifies, preserves, and reviews printer console output, Moonraker/Klipper state changes, restart boundaries, shutdown events, and diagnostic messages.

The product goal is to keep the context that normally disappears when firmware restarts, Klipper restarts, Moonraker reconnects, an MCU disconnects, or the live console resets.

## Goals

- Capture recent Moonraker/Klipper console and state output for configured printers.
- Preserve diagnostic context around fault events and restart boundaries.
- Support manual diagnostic sessions for intentional troubleshooting.
- Store data locally in SQLite with persistent Docker storage from day one.
- Provide bounded, searchable review screens that do not load unbounded log history.
- Keep API secrets server-side only.
- Document Moonraker API limitations honestly as they are verified.

## Non-Goals

- Cloud logging, remote telemetry, or hosted accounts.
- ML diagnosis or probabilistic root-cause scoring.
- Replacing Moonraker, Mainsail, Fluidd, Klipper, or system logs.
- Assuming historical console backfill exists before verifying the API.
- Loading full-day console logs into the browser without limits.

## Core Product Concepts

### Rolling Console Watch

Passive recent memory per printer. When enabled, ConsoleWatch records recent console/log output and prunes old rows based on a retention window such as 4, 8, 12, or 24 hours.

### Manual Diagnostic Session

Intentional user recording. A user can start and stop a session, label it, add notes, save it, discard it, and later review copied entries that survive rolling pruning.

### Event-Preserved Incident Capture

Automatic fault capture. Rule-based triggers preserve entries around an important message or state transition, including a visible trigger point. Preserved captures survive rolling pruning.

### Restart / Boundary Timeline

ConsoleWatch marks restart and reconnect boundaries such as Klippy disconnected, Klippy ready, Klippy shutdown, firmware restart commands, MCU reconnects, and Moonraker websocket disconnect/restored events.

## Architecture Plan

### Backend

- Python 3.13 runtime.
- FastAPI API server.
- SQLAlchemy models and SQLite persistence.
- Pydantic schemas.
- Service-layer modules for ingestion, classification, retention, sessions, preservation, restart boundaries, search/export, and health.
- Background worker / Moonraker connection manager in later phases.
- Docker-ready configuration through environment variables.

### Frontend

- React, TypeScript, and Vite.
- Routing-ready app shell.
- API helper with configurable base URL.
- Browser-local timezone formatting helper.
- Pages planned for dashboard, printers, live console watch, manual sessions, preserved captures, capture detail, global search, and settings/diagnostics.

### Deployment

- Docker Compose runs backend and frontend.
- SQLite database lives in a named Docker volume at `/data/consolewatch.db`.
- Frontend served by nginx with `index.html` and route fallbacks set to no-cache to reduce stale UI after redeploys.
- README documents local development, Docker Compose, Portainer persistence, backup/restore, and trusted LAN assumptions.

## Data Model Plan

Initial tables:

- `printers`
- `console_entries`
- `manual_log_sessions`
- `manual_session_entries`
- `preserved_console_captures`
- `preserved_console_entries`
- `detected_events`
- `restart_boundaries`

Indexes planned early:

- `console_entries(printer_id, captured_at)`
- `console_entries(classification)`
- `console_entries(level)`
- `console_entries(event_type)`
- `console_entries(captured_at)`

Important data rules:

- Store canonical timestamps in UTC.
- Return API timestamps with explicit timezone information.
- Display times in the browser timezone by default.
- Fallback timezone is `America/New_York`.
- Preserve original message text exactly where practical.
- Keep parsed/classified metadata separate from original messages.
- Keep useful raw payload JSON for debugging.

## Phased Implementation Plan

### Phase 0: Project Setup and Roadmap

- Create repository/folder.
- Create this roadmap before application code.
- Add README, `.env.example`, Docker Compose skeleton, backend folder, frontend folder, and docs folder.
- Connect local repo to `https://github.com/khisanthax/consolewatch`.
- Commit and push initial scaffold.

Definition of done:

- Roadmap exists and is detailed.
- README has initial setup notes.
- Project scaffold exists.
- Docker persistence plan is documented.
- Commit is pushed.

### Phase 1: Foundation

- FastAPI backend scaffold.
- React/Vite frontend scaffold.
- SQLite models/bootstrap.
- Printer profile CRUD.
- Basic app shell/navigation.
- Local timezone-safe formatting helper.
- Backend health endpoint.
- Frontend can call backend.
- Docker build path works or limitations documented.

Definition of done:

- User can create/edit/delete printer profiles.
- Data persists in SQLite.
- Frontend displays saved printers.
- Roadmap updated.

### Phase 2: Moonraker Connection and Ingestion Proof

- Add Moonraker client.
- Verify websocket notifications and available log endpoints.
- Connect to Moonraker websocket if practical.
- Capture `notify_gcode_response` or the best available real-time source.
- Store console entries.
- Show basic recent console page.
- Document Moonraker API limitations.

### Phase 3: Rolling Console Watch

- Per-printer watch toggle.
- Retention window selector.
- Automatic background ingestion for enabled printers.
- Connection manager for active printers.
- Rolling pruning job.
- Bounded UI table and recent-entry search/filtering.

### Phase 4: Manual Diagnostic Sessions

- Start/stop manual session.
- Save/discard completed session.
- Copy entries into active/saved sessions.
- Session list and detail pages.
- Session search/filtering.

### Phase 5: Event-Triggered Preservation

- Rule-based trigger engine.
- Detected events table.
- Preserve 30 minutes before trigger and continue 30 minutes after.
- Extend captures when another trigger occurs during the post-window.
- Preserve copied capture rows that survive pruning.
- Preserved captures list and detail pages.
- Trigger marker in console timeline.

### Phase 6: Restart and Firmware Boundary Handling

- Detect firmware restart, Klippy shutdown/disconnected/ready, Moonraker reconnect, and MCU reconnect boundaries where available.
- Create restart boundary records.
- Mark boundaries in timelines.
- Preserve around restart-related events.
- Control duplicate capture behavior during reconnect storms.

### Phase 7: Search and Export

- Global search across recent console entries, manual sessions, and preserved captures.
- Export preserved captures, manual sessions, and filtered results as `.txt`.
- Consider optional `.json` export later.

### Phase 8: Polish, Diagnostics, and Storage Visibility

- Better classifications.
- Configurable trigger rules.
- Dashboard counts.
- Storage usage view.
- Backup/restore docs.
- Optional notifications.
- Improved empty/loading/error states.

## Milestone Checklist

- [x] Phase 0 roadmap drafted.
- [x] Phase 0 scaffold created.
- [x] Phase 0 scaffold committed.
- [x] Phase 0 scaffold pushed.
- [ ] Phase 1 foundation complete.
- [ ] Phase 2 ingestion proof complete.
- [ ] Phase 3 rolling watch complete.
- [ ] Phase 4 manual sessions complete.
- [ ] Phase 5 preservation complete.
- [ ] Phase 6 restart boundaries complete.
- [ ] Phase 7 search/export complete.
- [ ] Phase 8 polish complete.
- [ ] MVP complete.

## Current Priority Slice

Current slice: Phase 0 initial scaffold.

Scope:

- Establish the repo structure.
- Document the roadmap and persistence decisions.
- Add minimal backend/frontend files that make the intended architecture clear.
- Commit and push the scaffold.

Out of scope for this slice:

- Printer CRUD.
- Moonraker websocket connection.
- Console ingestion.
- Persistence models beyond placeholders.
- Production validation of Docker builds.

## Decision Log

- 2026-06-07: Use TempWatch as an architecture template, but adapt naming, data model, and product language to console/log capture.
- 2026-06-07: Use a named Docker volume `consolewatch_data` mounted at `/data` so the default SQLite database survives container redeploys.
- 2026-06-07: Use `CONSOLEWATCH_` environment variable prefixes to avoid TempWatch carryover.
- 2026-06-07: Keep Moonraker API behavior unimplemented until Phase 2 verification; do not claim historical backfill support yet.
- 2026-06-07: Use copied rows for saved manual sessions and preserved captures unless a safer design is later proven.
- 2026-06-07: Configure nginx to avoid stale `index.html` caching from the first scaffold.

## Known Risks

- Moonraker may not provide full historical console backfill; ConsoleWatch may only capture from connection time.
- Console/log volume can grow quickly without strict retention, limits, indexes, and pruning.
- Reconnect storms could create duplicate preserved captures without suppression logic.
- Timezone handling can become misleading if UTC timestamps are returned or displayed incorrectly.
- Docker/Portainer persistence mistakes could cause data loss if users remove the volume.
- API key handling must remain backend-only.

## Open Questions

- Which Moonraker notification stream is most reliable for user-visible console/gcode responses?
- Can user-issued commands be observed reliably, or only responses and state changes?
- Which log endpoints are available through Moonraker without mounting host files?
- What metadata is available for current print filename and print state during every event?
- What default retention window should be selected for new printers?
- How much capture storm suppression is enough for common Klipper reconnect loops?

## Recent Completed Work Log

- 2026-06-07: Created initial roadmap with product concepts, architecture, data model plan, phases, risks, and current slice.
- 2026-06-07: Created initial backend/frontend/docs scaffold files.
- 2026-06-07: Pushed initial Phase 0 scaffold to GitHub.

## Upcoming Commit Targets

1. Phase 0 scaffold: roadmap, README, `.env.example`, Docker Compose, backend skeleton, frontend skeleton.
2. Phase 1A foundation: SQLAlchemy database bootstrap and printer model/schema.
3. Phase 1B foundation: printer CRUD API and frontend printer management page.
4. Phase 1C foundation: Docker build validation and frontend health/API smoke path.

## Validation Checklist

For each meaningful slice:

- [ ] Roadmap updated before commit.
- [ ] Backend import/compile check completed.
- [ ] Backend smoke test completed when behavior exists.
- [ ] Frontend production build completed when frontend behavior changes.
- [ ] Docker Compose validation completed or limitation documented.
- [ ] Git diff reviewed.
- [ ] Commit created.
- [ ] Commit pushed.

Phase 0 validation status:

- [x] Roadmap created before application code.
- [x] Backend import/compile check.
- [x] Frontend production build.
- [x] Git diff reviewed.
- [x] Commit created.
- [x] Commit pushed.

## Deployment Notes

- Default backend database path in Docker is `sqlite:////data/consolewatch.db`.
- Default Docker volume is `consolewatch_data`.
- Removing the Docker volume removes the SQLite database and all ConsoleWatch data.
- For bind-mount deployments, mount a host folder to `/data`.
- Frontend `index.html` and route fallback are served with no-cache headers to reduce stale UI after redeploys.
- Static asset files under `/assets/` may be cached long-term because Vite fingerprints production assets.
- ConsoleWatch assumes a trusted LAN deployment and does not add internet-facing authentication in the early scaffold.

## Limitations Discovered During Implementation

- No Moonraker API behavior has been verified yet.
- Historical console backfill support is unknown.
- Docker builds have not been validated yet in Phase 0.
- The current backend/frontend are scaffolds only and do not yet implement printer CRUD or persistence.
- Initial frontend build required an explicit Vite client type declaration for `import.meta.env`; this is now included in `frontend/src/vite-env.d.ts`.
