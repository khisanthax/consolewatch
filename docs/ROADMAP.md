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
- [x] Phase 1 foundation complete.
- [x] Phase 2 ingestion proof complete.
- [x] Phase 3 rolling watch complete.
- [x] Phase 4 manual sessions complete.
- [x] Phase 5 preservation complete.
- [x] Phase 6 restart boundaries complete.
- [x] Phase 7 search/export complete.
- [ ] Phase 8 polish complete.
- [ ] MVP complete.

## Current Priority Slice

Current slice: Phase 8 polish, diagnostics, and storage visibility validation.

Scope:

- Add dashboard counts for printers, rolling entries, sessions, preserved captures, detected events, and restart boundaries.
- Add storage visibility for SQLite database path, existence, and size where available.
- Add diagnostics/settings API that exposes non-secret runtime configuration and trigger rule visibility.
- Improve settings/diagnostics UI with backup/restore, Docker persistence, frontend cache, trusted LAN, and validation notes.
- Improve empty/loading/error states in dashboard and settings surfaces.
- Keep Moonraker API keys and other secrets out of diagnostic responses.
- Validate diagnostics behavior with backend tests and frontend build.
- Document limitations honestly.
- Commit and push the completed polish/diagnostics slice.

Out of scope for this slice:

- Full historical backfill unless current Moonraker APIs prove it is available.
- Advanced configurable trigger rules.
- Deep firmware/Moonraker causality analysis beyond explicit boundary markers.
- `.json` exports.
- Virtualized result rendering.
- Internet-facing authentication.

## Decision Log

- 2026-06-07: Use TempWatch as an architecture template, but adapt naming, data model, and product language to console/log capture.
- 2026-06-07: Use a named Docker volume `consolewatch_data` mounted at `/data` so the default SQLite database survives container redeploys.
- 2026-06-07: Use `CONSOLEWATCH_` environment variable prefixes to avoid TempWatch carryover.
- 2026-06-07: Keep Moonraker API behavior unimplemented until Phase 2 verification; do not claim historical backfill support yet.
- 2026-06-07: Use copied rows for saved manual sessions and preserved captures unless a safer design is later proven.
- 2026-06-07: Configure nginx to avoid stale `index.html` caching from the first scaffold.
- 2026-06-07: Started Phase 1 foundation with printer CRUD as the first persistent user-facing behavior.
- 2026-06-07: Docker Compose validation could not run locally because the `docker` CLI is not available on PATH in this shell.
- 2026-06-07: Started Phase 2 ingestion proof; current priority is verified Moonraker notification ingestion and bounded recent-console review.
- 2026-06-07: Verified from official Moonraker docs that websocket connections receive server-generated gcode response events and JSON-RPC notifications.
- 2026-06-07: Verified `notify_gcode_response`, `notify_status_update`, `notify_klippy_ready`, `notify_klippy_shutdown`, and `notify_klippy_disconnected` as initial Phase 2 ingestion sources.
- 2026-06-07: Live Moonraker websocket ingestion is represented by a client shell and tested payload conversion; no live printer was available for end-to-end connection testing.
- 2026-06-07: Started Phase 3 rolling console watch; current priority is background ingestion for watch-enabled printers plus retention pruning.
- 2026-06-07: Added a background rolling watch manager that starts one websocket task per enabled watched printer and records supported Moonraker notifications.
- 2026-06-07: Added rolling pruning for `console_entries` only; manual session and preserved capture copy tables remain untouched by pruning.
- 2026-06-07: Added watch status and manual prune endpoints for observability and validation.
- 2026-06-07: Started Phase 4 manual diagnostic sessions; current priority is active session recording with copied entry rows.
- 2026-06-07: Implemented manual session start/stop/save/discard behavior and copied active-session entries from newly ingested console entries.
- 2026-06-07: Saved manual sessions use copied rows in `manual_session_entries`, so they survive rolling pruning of `console_entries`.
- 2026-06-07: Started Phase 5 event-triggered preservation; current priority is explicit trigger rules and copied preserved capture rows.
- 2026-06-07: Implemented explicit trigger rules for error-like console entries and Klippy state events.
- 2026-06-07: Implemented detected events, preserved capture creation/extension, copied preserved entries, and trigger-entry marking.
- 2026-06-07: Started Phase 6 restart and firmware boundary handling; current priority is durable boundary records plus timeline markers.
- 2026-06-07: Implemented restart boundary records for Klippy state notifications and restart-like console messages.
- 2026-06-07: Added duplicate suppression for same-type printer boundaries within a reconnect-storm window.
- 2026-06-07: Recent console and preserved capture timelines now expose boundary markers.
- 2026-06-07: Started Phase 7 search and export; current priority is bounded global search and readable `.txt` exports.
- 2026-06-07: Implemented bounded global search across rolling console entries, manual session copies, and preserved capture copies.
- 2026-06-07: Implemented `.txt` exports for filtered search results, manual sessions, and preserved captures.
- 2026-06-08: Started Phase 8 polish, diagnostics, and storage visibility; current priority is dashboard/storage diagnostics plus final documentation.
- 2026-06-08: Implemented Phase 8 diagnostics API with non-secret runtime settings, trigger rule visibility, storage metadata, and record counts.
- 2026-06-08: Added dashboard summary counts and settings diagnostics/storage panels.
- 2026-06-08: Phase 8 Docker validation could not run locally because the `docker` CLI is still unavailable on PATH in this shell.

## Known Risks

- Moonraker may not provide full historical console backfill; ConsoleWatch may only capture from connection time.
- Console/log volume can grow quickly without strict retention, limits, indexes, and pruning.
- Reconnect storms could create duplicate preserved captures without suppression logic.
- Timezone handling can become misleading if UTC timestamps are returned or displayed incorrectly.
- Docker/Portainer persistence mistakes could cause data loss if users remove the volume.
- API key handling must remain backend-only.

## Open Questions

- Which Moonraker notification stream is most reliable for user-visible console/gcode responses?
- Answered for Phase 2: official Moonraker docs state that all Klippy gcode responses are forwarded over websocket as `notify_gcode_response`.
- Can user-issued commands be observed reliably, or only responses and state changes?
- Which log endpoints are available through Moonraker without mounting host files?
- What metadata is available for current print filename and print state during every event?
- What default retention window should be selected for new printers?
- How much capture storm suppression is enough for common Klipper reconnect loops?

## Recent Completed Work Log

- 2026-06-07: Created initial roadmap with product concepts, architecture, data model plan, phases, risks, and current slice.
- 2026-06-07: Created initial backend/frontend/docs scaffold files.
- 2026-06-07: Pushed initial Phase 0 scaffold to GitHub.
- 2026-06-07: Implemented initial SQLite table bootstrap for printers, console entries, manual sessions, preserved captures, detected events, and restart boundaries.
- 2026-06-07: Implemented printer profile CRUD API with API keys accepted server-side but excluded from responses.
- 2026-06-07: Implemented frontend printer management with create, edit, delete, retention selector, watch toggle, backend health, and local timestamp formatting.
- 2026-06-07: Implemented Moonraker notification ingestion for gcode responses, Klippy state notifications, and selected status updates.
- 2026-06-07: Implemented bounded recent console API and frontend console review page with mock notification ingestion.
- 2026-06-07: Implemented rolling watch background manager, retention pruning, watch status/prune APIs, and live console watch status UI.
- 2026-06-07: Implemented manual diagnostic session APIs, active entry copying, session list/detail UI, and session filtering.
- 2026-06-07: Implemented event-triggered preserved captures, detected events, capture detail API, and preserved capture review UI.
- 2026-06-07: Implemented restart boundary detection, entry linkage, duplicate suppression, and UI boundary markers.
- 2026-06-07: Implemented global search API/UI and text exports for search results, manual sessions, and preserved captures.
- 2026-06-08: Implemented diagnostics API/UI, storage visibility, dashboard counts, and deployment notes for Phase 8 polish.

## Upcoming Commit Targets

1. Phase 8 final sync: mark roadmap completion after the implementation commit is pushed.
2. MVP hardening: validate Docker on a host with Docker available.
3. MVP hardening: run end-to-end Moonraker websocket validation against a live printer.

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
- Docker builds have not been validated yet because the local `docker` CLI is unavailable in this shell.
- Live Moonraker websocket connectivity has not been end-to-end tested because no live printer is available in this environment.
- The mock ingest endpoint is for Phase 2 validation and may be replaced or gated before broader deployment.
- Phase 3 background watch behavior is validated at service/API level, not against a live Moonraker websocket.
- Phase 4 manual sessions copy newly ingested entries only while active; they do not backfill older rolling entries from before the session start.
- Phase 5 preservation copies entries currently present in rolling `console_entries`; if the rolling table was already pruned before a trigger, older pre-trigger context cannot be recovered.
- Phase 6 boundary detection is rule-based and limited to explicit Klippy state notifications plus restart/disconnect/reconnect-like messages.
- Phase 7 search/export is bounded by explicit limits; it is not a full unbounded archive dump.
- Initial frontend build required an explicit Vite client type declaration for `import.meta.env`; this is now included in `frontend/src/vite-env.d.ts`.
- Phase 8 diagnostics can only report SQLite file size when the backend can resolve and access a file-backed SQLite database path.

Phase 1 validation status:

- [x] Roadmap updated before coding.
- [x] SQLite models/bootstrap implemented.
- [x] Printer profile CRUD API implemented.
- [x] Frontend printer management implemented.
- [x] Backend import/compile check passed.
- [x] Backend printer CRUD API test passed.
- [x] Frontend production build passed.
- [x] Docker Compose validation attempted.
- [ ] Docker Compose validation passed.
- [x] Git diff reviewed.
- [x] Commit created.
- [x] Commit pushed.

Phase 3 validation status:

- [x] Roadmap updated before coding.
- [x] Background watch manager implemented.
- [x] Retention pruning implemented.
- [x] Watch status and manual prune APIs implemented.
- [x] Live console watch status UI implemented.
- [x] Backend import/compile check passed.
- [x] Backend tests passed.
- [x] Frontend production build passed.
- [x] Docker Compose validation attempted.
- [ ] Docker Compose validation passed.
- [ ] Live Moonraker websocket tested.
- [x] Git diff reviewed.
- [x] Commit created.
- [x] Commit pushed.

Phase 2 validation status:

- [x] Roadmap updated before coding.
- [x] Official Moonraker websocket notification docs checked.
- [x] Moonraker notification-to-console-entry ingestion implemented.
- [x] Recent console API implemented with bounded limits.
- [x] Recent console frontend implemented.
- [x] Mock Moonraker payload ingestion validated.
- [x] Backend import/compile check passed.
- [x] Backend tests passed.
- [x] Frontend production build passed.
- [x] Docker Compose validation attempted.
- [ ] Docker Compose validation passed.
- [x] Git diff reviewed.
- [x] Commit created.
- [x] Commit pushed.

Phase 4 validation status:

- [x] Roadmap updated before coding.
- [x] Manual session start/stop/save/discard API implemented.
- [x] Active session entry copying implemented.
- [x] Session list/detail API implemented with bounded filters.
- [x] Manual sessions frontend implemented.
- [x] Saved session survives rolling pruning test passed.
- [x] Backend import/compile check passed.
- [x] Backend tests passed.
- [x] Frontend production build passed.
- [x] Docker Compose validation attempted.
- [ ] Docker Compose validation passed.
- [x] Git diff reviewed.
- [x] Commit created.
- [x] Commit pushed.

Phase 5 validation status:

- [x] Roadmap updated before coding.
- [x] Rule-based trigger engine implemented.
- [x] Detected events writes implemented.
- [x] Preserved capture create/extend behavior implemented.
- [x] Preserved entry copying and trigger marker implemented.
- [x] Preserved captures list/detail API implemented.
- [x] Preserved captures frontend implemented.
- [x] Preservation survives rolling pruning test passed.
- [x] Backend import/compile check passed.
- [x] Backend tests passed.
- [x] Frontend production build passed.
- [x] Docker Compose validation attempted.
- [ ] Docker Compose validation passed.
- [x] Git diff reviewed.
- [x] Commit created.
- [x] Commit pushed.

Phase 6 validation status:

- [x] Roadmap updated before coding.
- [x] Restart boundary records implemented.
- [x] Console entry boundary linkage implemented.
- [x] Duplicate boundary suppression implemented.
- [x] Recent console timeline boundary markers implemented.
- [x] Preserved capture boundary markers implemented.
- [x] Backend import/compile check passed.
- [x] Backend tests passed.
- [x] Frontend production build passed.
- [x] Docker Compose validation attempted.
- [ ] Docker Compose validation passed.
- [ ] Live Moonraker websocket tested.
- [x] Git diff reviewed.
- [x] Commit created.
- [x] Commit pushed.

Phase 7 validation status:

- [x] Roadmap updated before coding.
- [x] Global bounded search API implemented.
- [x] Global search frontend implemented.
- [x] Filtered search `.txt` export implemented.
- [x] Manual session `.txt` export implemented.
- [x] Preserved capture `.txt` export implemented.
- [x] Backend import/compile check passed.
- [x] Backend tests passed.
- [x] Frontend production build passed.
- [x] Docker Compose validation attempted.
- [ ] Docker Compose validation passed.
- [x] Git diff reviewed.
- [x] Commit created.
- [x] Commit pushed.

Phase 8 validation status:

- [x] Roadmap updated before coding.
- [x] Diagnostics API implemented.
- [x] Diagnostics service excludes secrets from responses.
- [x] Storage path/existence/size visibility implemented.
- [x] Dashboard counts implemented.
- [x] Settings diagnostics UI implemented.
- [x] Backend import/compile check passed.
- [x] Backend tests passed.
- [x] Frontend production build passed.
- [x] Docker Compose validation attempted.
- [ ] Docker Compose validation passed.
- [x] Git diff reviewed.
- [ ] Commit created.
- [ ] Commit pushed.
