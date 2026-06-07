import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  discardManualSession,
  exportUrl,
  getManualSession,
  listManualSessions,
  listPrinters,
  ManualSession,
  ManualSessionDetail,
  Printer,
  saveManualSession,
  startManualSession,
  stopManualSession
} from "../lib/api";
import { formatLocalDateTime, formatOptionalLocalDateTime } from "../lib/time";

export default function ManualSessionsPage() {
  const [printers, setPrinters] = useState<Printer[]>([]);
  const [sessions, setSessions] = useState<ManualSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<ManualSessionDetail | null>(null);
  const [printerId, setPrinterId] = useState("");
  const [label, setLabel] = useState("");
  const [notes, setNotes] = useState("");
  const [search, setSearch] = useState("");
  const [classification, setClassification] = useState("");
  const [source, setSource] = useState("");
  const [level, setLevel] = useState("");
  const [limit, setLimit] = useState(250);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const sortedPrinters = useMemo(() => [...printers].sort((a, b) => a.name.localeCompare(b.name)), [printers]);
  const activeSessions = sessions.filter((session) => session.status === "active");

  async function refreshSessions(nextSelectedId = selectedSession?.id) {
    setIsLoading(true);
    setError(null);
    try {
      const result = await listManualSessions();
      setSessions(result);
      if (nextSelectedId) {
        const exists = result.some((session) => session.id === nextSelectedId);
        setSelectedSession(exists ? await getManualSession(nextSelectedId, { search, classification, source, level, limit }) : null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sessions");
    } finally {
      setIsLoading(false);
    }
  }

  async function refreshDetail(sessionId: number) {
    setError(null);
    try {
      setSelectedSession(await getManualSession(sessionId, { search, classification, source, level, limit }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load session detail");
    }
  }

  useEffect(() => {
    listPrinters()
      .then((result) => {
        setPrinters(result);
        if (!printerId && result.length > 0) {
          setPrinterId(String(result[0].id));
        }
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load printers"));
    void refreshSessions();
  }, []);

  async function handleStart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!printerId) {
      setError("Select a printer before starting a session.");
      return;
    }

    setError(null);
    try {
      const started = await startManualSession({
        printer_id: Number(printerId),
        label: label.trim() || "Manual diagnostic session",
        notes: notes.trim() || null
      });
      setLabel("");
      setNotes("");
      await refreshSessions(started.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start session");
    }
  }

  async function handleStop(session: ManualSession) {
    await stopManualSession(session.id);
    await refreshSessions(session.id);
  }

  async function handleSave(session: ManualSession) {
    await saveManualSession(session.id);
    await refreshSessions(session.id);
  }

  async function handleDiscard(session: ManualSession) {
    const confirmed = window.confirm(`Discard ${session.label}? Copied session entries will be deleted.`);
    if (!confirmed) {
      return;
    }
    await discardManualSession(session.id);
    await refreshSessions(undefined);
  }

  async function handleDetailFilter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedSession) {
      await refreshDetail(selectedSession.id);
    }
  }

  return (
    <section className="page">
      <header>
        <p className="eyebrow">Sessions</p>
        <h2>Manual diagnostic sessions</h2>
      </header>

      <div className="split-layout sessions-layout">
        <div className="panel form-panel">
          <h3>Start session</h3>
          <form className="form-panel nested-form" onSubmit={handleStart}>
            <label>
              <span>Printer</span>
              <select value={printerId} onChange={(event) => setPrinterId(event.target.value)}>
                {sortedPrinters.map((printer) => (
                  <option key={printer.id} value={printer.id}>
                    {printer.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Label</span>
              <input value={label} onChange={(event) => setLabel(event.target.value)} placeholder="Probe calibration test" />
            </label>
            <label>
              <span>Notes</span>
              <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={5} />
            </label>
            <button type="submit">Start Session</button>
          </form>

          <div className="watch-summary">
            <h3>Active</h3>
            <p>{activeSessions.length} active session{activeSessions.length === 1 ? "" : "s"}</p>
          </div>
          {error && <p className="error-text">{error}</p>}
        </div>

        <div className="panel table-panel">
          <div className="panel-heading">
            <h3>Sessions</h3>
            <button type="button" className="secondary-button" onClick={() => void refreshSessions()}>
              Refresh
            </button>
          </div>
          {isLoading && <p>Loading sessions...</p>}
          {!isLoading && sessions.length === 0 && <p>No manual sessions yet.</p>}
          {!isLoading && sessions.length > 0 && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Session</th>
                    <th>Printer</th>
                    <th>Status</th>
                    <th>Entries</th>
                    <th>Started</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((session) => (
                    <tr key={session.id}>
                      <td>
                        <strong>{session.label}</strong>
                        {session.notes && <small>{session.notes}</small>}
                      </td>
                      <td>{session.printer_name ?? session.printer_id}</td>
                      <td>
                        <span className="pill">{session.status}</span>
                      </td>
                      <td>{session.entry_count}</td>
                      <td>
                        {formatLocalDateTime(session.started_at)}
                        <small>Ended {formatOptionalLocalDateTime(session.ended_at)}</small>
                      </td>
                      <td>
                        <div className="row-actions">
                          <button type="button" className="secondary-button" onClick={() => void refreshDetail(session.id)}>
                            Open
                          </button>
                          {session.status === "active" && (
                            <button type="button" className="secondary-button" onClick={() => void handleStop(session)}>
                              Stop
                            </button>
                          )}
                          {session.status === "stopped" && (
                            <button type="button" onClick={() => void handleSave(session)}>
                              Save
                            </button>
                          )}
                          <button type="button" className="danger-button" onClick={() => void handleDiscard(session)}>
                            Discard
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {selectedSession && (
        <div className="panel table-panel">
          <div className="panel-heading">
            <div>
              <h3>{selectedSession.label}</h3>
              <p>
                {selectedSession.status} / {selectedSession.entry_count} copied entries
              </p>
            </div>
            <button type="button" className="secondary-button" onClick={() => void refreshDetail(selectedSession.id)}>
              Refresh Detail
            </button>
            <button
              type="button"
              className="secondary-button"
              onClick={() => window.open(exportUrl(`/exports/manual-session/${selectedSession.id}.txt`), "_blank")}
            >
              Export TXT
            </button>
          </div>
          <form className="filter-row" onSubmit={handleDetailFilter}>
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search session" />
            <select value={classification} onChange={(event) => setClassification(event.target.value)}>
              <option value="">Any class</option>
              <option value="normal">normal</option>
              <option value="heater">heater</option>
              <option value="adc">adc</option>
              <option value="shutdown">shutdown</option>
              <option value="disconnect">disconnect</option>
            </select>
            <select value={source} onChange={(event) => setSource(event.target.value)}>
              <option value="">Any source</option>
              <option value="gcode_response">gcode_response</option>
              <option value="klippy_state">klippy_state</option>
            </select>
            <select value={level} onChange={(event) => setLevel(event.target.value)}>
              <option value="">Any level</option>
              <option value="info">info</option>
              <option value="warning">warning</option>
              <option value="error">error</option>
            </select>
            <select value={limit} onChange={(event) => setLimit(Number(event.target.value))}>
              <option value={100}>100</option>
              <option value={250}>250</option>
              <option value={500}>500</option>
            </select>
            <button type="submit">Apply</button>
          </form>
          {selectedSession.entries.length === 0 && <p>No copied entries match the current filters.</p>}
          {selectedSession.entries.length > 0 && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Level</th>
                    <th>Source</th>
                    <th>Classification</th>
                    <th>Message</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedSession.entries.map((entry) => (
                    <tr key={entry.id}>
                      <td>{formatLocalDateTime(entry.captured_at)}</td>
                      <td>
                        <span className={`pill level-${entry.level}`}>{entry.level}</span>
                      </td>
                      <td>{entry.source}</td>
                      <td>{entry.classification}</td>
                      <td className="message-cell">{entry.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
