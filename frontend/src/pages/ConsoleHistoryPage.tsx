import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  ConsoleEntry,
  ingestMoonrakerNotification,
  listConsoleEntries,
  listPrinters,
  Printer,
  pruneWatchEntries
} from "../lib/api";
import { formatLocalDateTime } from "../lib/time";

const sampleNotification = JSON.stringify(
  {
    jsonrpc: "2.0",
    method: "notify_gcode_response",
    params: ["!! ADC out of range"]
  },
  null,
  2
);

export default function ConsoleHistoryPage() {
  const [printers, setPrinters] = useState<Printer[]>([]);
  const [entries, setEntries] = useState<ConsoleEntry[]>([]);
  const [selectedPrinterId, setSelectedPrinterId] = useState("");
  const [search, setSearch] = useState("");
  const [classification, setClassification] = useState("");
  const [source, setSource] = useState("");
  const [level, setLevel] = useState("");
  const [limit, setLimit] = useState(100);
  const [mockPayload, setMockPayload] = useState(sampleNotification);
  const [lastPruneResult, setLastPruneResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const printerOptions = useMemo(
    () => [...printers].sort((a, b) => a.name.localeCompare(b.name)),
    [printers]
  );

  async function refreshEntries() {
    setIsLoading(true);
    setError(null);
    try {
      const parsedPrinterId = selectedPrinterId ? Number(selectedPrinterId) : undefined;
      setEntries(
        await listConsoleEntries({
          printer_id: parsedPrinterId,
          search,
          classification,
          source,
          level,
          limit
        })
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load console history");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    listPrinters()
      .then((result) => {
        setPrinters(result);
        if (!selectedPrinterId && result.length > 0) {
          setSelectedPrinterId(String(result[0].id));
        }
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load printers");
      });
  }, []);

  useEffect(() => {
    void refreshEntries();
  }, [selectedPrinterId, classification, source, level, limit]);

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await refreshEntries();
  }

  async function handleMockIngest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      setError("Add or select a printer before ingesting a mock notification.");
      return;
    }

    setError(null);
    try {
      const parsed = JSON.parse(mockPayload);
      await ingestMoonrakerNotification(Number(selectedPrinterId), parsed);
      await refreshEntries();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to ingest mock notification");
    }
  }

  async function handlePrune() {
    setError(null);
    try {
      const result = await pruneWatchEntries();
      setLastPruneResult(`Deleted ${result.deleted_total} continuous watch entries`);
      await refreshEntries();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to prune continuous watch entries");
    }
  }

  return (
    <section className="page">
      <header>
        <p className="eyebrow">Console History</p>
        <h2>Past continuous watch entries</h2>
      </header>

      <div className="panel form-panel">
        <h3>Filters</h3>
        <form className="filter-row search-filter-row" onSubmit={handleSearch}>
          <select value={selectedPrinterId} onChange={(event) => setSelectedPrinterId(event.target.value)}>
            <option value="">All printers</option>
            {printerOptions.map((printer) => (
              <option key={printer.id} value={printer.id}>
                {printer.name}
              </option>
            ))}
          </select>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="heater, probe, mcu" />
          <select value={classification} onChange={(event) => setClassification(event.target.value)}>
            <option value="">Any class</option>
            <option value="normal">normal</option>
            <option value="adc">adc</option>
            <option value="shutdown">shutdown</option>
            <option value="disconnect">disconnect</option>
            <option value="reconnect">reconnect</option>
            <option value="heater">heater</option>
            <option value="thermal">thermal</option>
            <option value="mcu">mcu</option>
            <option value="probe">probe</option>
            <option value="endstop">endstop</option>
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
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={250}>250</option>
            <option value={500}>500</option>
          </select>
          <button type="submit" disabled={isLoading}>
            {isLoading ? "Loading" : "Apply"}
          </button>
        </form>
        <div className="button-row">
          <button type="button" className="secondary-button" onClick={() => void refreshEntries()}>
            Refresh
          </button>
          <button type="button" className="secondary-button" onClick={() => void handlePrune()}>
            Run Prune
          </button>
        </div>
        {lastPruneResult && <p>{lastPruneResult}</p>}
        {error && <p className="error-text">{error}</p>}
      </div>

      <div className="panel table-panel">
        <div className="panel-heading">
          <h3>Continuous watch history</h3>
          <span className="pill">{entries.length}</span>
        </div>
        {isLoading && <p>Loading console history...</p>}
        {!isLoading && entries.length === 0 && <p>No retained continuous watch entries found.</p>}
        {!isLoading && entries.length > 0 && (
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
                {entries.map((entry) => (
                  <tr key={entry.id} className={entry.boundary_type ? "boundary-row" : undefined}>
                    <td>{formatLocalDateTime(entry.captured_at)}</td>
                    <td>
                      <span className={`pill level-${entry.level}`}>{entry.level}</span>
                    </td>
                    <td>{entry.source}</td>
                    <td>{entry.classification}</td>
                    <td className="message-cell">
                      {entry.message}
                      {(entry.event_type || entry.filename) && (
                        <small>{[entry.event_type, entry.filename].filter(Boolean).join(" / ")}</small>
                      )}
                      {entry.boundary_type && <small>Boundary: {entry.boundary_type}</small>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <form className="panel form-panel mock-form" onSubmit={handleMockIngest}>
        <h3>Mock Moonraker ingest</h3>
        <label>
          <span>JSON-RPC notification</span>
          <textarea value={mockPayload} onChange={(event) => setMockPayload(event.target.value)} rows={9} />
        </label>
        <button type="submit">Ingest Mock</button>
      </form>
    </section>
  );
}
