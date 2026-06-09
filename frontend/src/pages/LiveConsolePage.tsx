import { useEffect, useMemo, useState } from "react";

import { ConsoleEntry, getWatchStatus, listConsoleEntries, listPrinters, Printer, WatchStatus } from "../lib/api";
import { formatLocalDateTime } from "../lib/time";

export default function LiveConsolePage() {
  const [printers, setPrinters] = useState<Printer[]>([]);
  const [entries, setEntries] = useState<ConsoleEntry[]>([]);
  const [selectedPrinterId, setSelectedPrinterId] = useState("");
  const [watchStatus, setWatchStatus] = useState<WatchStatus | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const printerOptions = useMemo(
    () => [...printers].sort((a, b) => a.name.localeCompare(b.name)),
    [printers]
  );

  async function refreshLiveEntries() {
    setIsLoading(true);
    setError(null);
    try {
      const parsedPrinterId = selectedPrinterId ? Number(selectedPrinterId) : undefined;
      setEntries(await listConsoleEntries({ printer_id: parsedPrinterId, limit: 25 }));
      setWatchStatus(await getWatchStatus());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load live console entries");
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
    void refreshLiveEntries();
  }, [selectedPrinterId]);

  useEffect(() => {
    if (!autoRefresh) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void refreshLiveEntries();
    }, 5000);
    return () => window.clearInterval(intervalId);
  }, [autoRefresh, selectedPrinterId]);

  return (
    <section className="page">
      <header>
        <p className="eyebrow">Live Console</p>
        <h2>What is happening now</h2>
      </header>

      <div className="panel">
        <div className="watch-summary">
          <h3>Live feed</h3>
          <dl>
            <div>
              <dt>Worker</dt>
              <dd>{watchStatus?.background_watch_enabled ? "Enabled" : "Disabled"}</dd>
            </div>
            <div>
              <dt>Watched printers</dt>
              <dd>{watchStatus?.watched_printer_count ?? 0}</dd>
            </div>
            <div>
              <dt>Active tasks</dt>
              <dd>{watchStatus?.task_count ?? 0}</dd>
            </div>
          </dl>
          <div className="filter-row search-filter-row">
            <select value={selectedPrinterId} onChange={(event) => setSelectedPrinterId(event.target.value)}>
              <option value="">All printers</option>
              {printerOptions.map((printer) => (
                <option key={printer.id} value={printer.id}>
                  {printer.name}
                </option>
              ))}
            </select>
            <label className="inline-toggle">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(event) => setAutoRefresh(event.target.checked)}
              />
              <span>Auto-refresh</span>
            </label>
            <button type="button" className="secondary-button" onClick={() => void refreshLiveEntries()}>
              Refresh
            </button>
          </div>
          {error && <p className="error-text">{error}</p>}
        </div>
      </div>

      <div className="panel table-panel">
        <div className="panel-heading">
          <h3>Latest entries</h3>
          {isLoading && <span className="pill">Loading</span>}
        </div>
        {!isLoading && entries.length === 0 && <p>No live console entries found.</p>}
        {entries.length > 0 && (
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
                      {entry.boundary_type && <small>Boundary: {entry.boundary_type}</small>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
