import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  getPreservedCapture,
  listPreservedCaptures,
  listPrinters,
  PreservedCapture,
  PreservedCaptureDetail,
  Printer
} from "../lib/api";
import { formatLocalDateTime } from "../lib/time";

export default function PreservedCapturesPage() {
  const [printers, setPrinters] = useState<Printer[]>([]);
  const [captures, setCaptures] = useState<PreservedCapture[]>([]);
  const [selectedCapture, setSelectedCapture] = useState<PreservedCaptureDetail | null>(null);
  const [printerId, setPrinterId] = useState("");
  const [search, setSearch] = useState("");
  const [classification, setClassification] = useState("");
  const [source, setSource] = useState("");
  const [level, setLevel] = useState("");
  const [limit, setLimit] = useState(500);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const sortedPrinters = useMemo(() => [...printers].sort((a, b) => a.name.localeCompare(b.name)), [printers]);

  async function refreshCaptures(nextSelectedId = selectedCapture?.id) {
    setIsLoading(true);
    setError(null);
    try {
      const parsedPrinterId = printerId ? Number(printerId) : undefined;
      const result = await listPreservedCaptures({ printer_id: parsedPrinterId, limit: 100 });
      setCaptures(result);
      if (nextSelectedId && result.some((capture) => capture.id === nextSelectedId)) {
        await refreshDetail(nextSelectedId);
      } else if (!nextSelectedId) {
        setSelectedCapture(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load preserved captures");
    } finally {
      setIsLoading(false);
    }
  }

  async function refreshDetail(captureId: number) {
    setError(null);
    try {
      setSelectedCapture(await getPreservedCapture(captureId, { search, classification, source, level, limit }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load preserved capture");
    }
  }

  useEffect(() => {
    listPrinters()
      .then(setPrinters)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load printers"));
    void refreshCaptures();
  }, []);

  useEffect(() => {
    void refreshCaptures(selectedCapture?.id);
  }, [printerId]);

  async function handleDetailFilter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedCapture) {
      await refreshDetail(selectedCapture.id);
    }
  }

  return (
    <section className="page">
      <header>
        <p className="eyebrow">Captures</p>
        <h2>Preserved incidents</h2>
      </header>

      <div className="split-layout sessions-layout">
        <div className="panel form-panel">
          <h3>Filters</h3>
          <label>
            <span>Printer</span>
            <select value={printerId} onChange={(event) => setPrinterId(event.target.value)}>
              <option value="">All printers</option>
              {sortedPrinters.map((printer) => (
                <option key={printer.id} value={printer.id}>
                  {printer.name}
                </option>
              ))}
            </select>
          </label>
          <button type="button" className="secondary-button" onClick={() => void refreshCaptures()}>
            Refresh Captures
          </button>
          {error && <p className="error-text">{error}</p>}
        </div>

        <div className="panel table-panel">
          <div className="panel-heading">
            <h3>Preserved captures</h3>
            <span className="pill">{captures.length}</span>
          </div>
          {isLoading && <p>Loading captures...</p>}
          {!isLoading && captures.length === 0 && <p>No preserved captures yet.</p>}
          {!isLoading && captures.length > 0 && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Trigger</th>
                    <th>Printer</th>
                    <th>Window</th>
                    <th>Entries</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {captures.map((capture) => (
                    <tr key={capture.id}>
                      <td>
                        <strong>{capture.trigger_type}</strong>
                        <small>{capture.trigger_message}</small>
                        <small>{formatLocalDateTime(capture.triggered_at)}</small>
                      </td>
                      <td>{capture.printer_name ?? capture.printer_id}</td>
                      <td>
                        {formatLocalDateTime(capture.started_at)}
                        <small>to {formatLocalDateTime(capture.ended_at)}</small>
                      </td>
                      <td>{capture.entry_count}</td>
                      <td>
                        <span className="pill">{capture.status}</span>
                      </td>
                      <td>
                        <button type="button" className="secondary-button" onClick={() => void refreshDetail(capture.id)}>
                          Open
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {selectedCapture && (
        <div className="panel table-panel">
          <div className="panel-heading">
            <div>
              <h3>{selectedCapture.trigger_type}</h3>
              <p>{selectedCapture.trigger_reason}</p>
            </div>
            <button type="button" className="secondary-button" onClick={() => void refreshDetail(selectedCapture.id)}>
              Refresh Detail
            </button>
          </div>

          {selectedCapture.detected_events.length > 0 && (
            <div className="event-strip">
              {selectedCapture.detected_events.map((event) => (
                <span key={event.id} className="pill level-error">
                  {event.event_type} / {formatLocalDateTime(event.captured_at)}
                </span>
              ))}
            </div>
          )}

          <form className="filter-row" onSubmit={handleDetailFilter}>
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search capture" />
            <select value={classification} onChange={(event) => setClassification(event.target.value)}>
              <option value="">Any class</option>
              <option value="normal">normal</option>
              <option value="heater">heater</option>
              <option value="adc">adc</option>
              <option value="shutdown">shutdown</option>
              <option value="disconnect">disconnect</option>
              <option value="timer">timer</option>
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
              <option value={250}>250</option>
              <option value={500}>500</option>
              <option value={1000}>1000</option>
            </select>
            <button type="submit">Apply</button>
          </form>

          {selectedCapture.entries.length === 0 && <p>No preserved entries match the current filters.</p>}
          {selectedCapture.entries.length > 0 && (
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
                  {selectedCapture.entries.map((entry) => (
                    <tr
                      key={entry.id}
                      className={[entry.is_trigger_entry ? "trigger-row" : "", entry.boundary_type ? "boundary-row" : ""]
                        .filter(Boolean)
                        .join(" ")}
                    >
                      <td>
                        {formatLocalDateTime(entry.captured_at)}
                        {entry.is_trigger_entry && <small>Trigger point</small>}
                        {entry.boundary_type && <small>Boundary: {entry.boundary_type}</small>}
                      </td>
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
