import { FormEvent, useEffect, useMemo, useState } from "react";

import { exportUrl, globalSearch, GlobalSearchResult, listPrinters, Printer } from "../lib/api";
import { formatLocalDateTime } from "../lib/time";

export default function SearchPage() {
  const [printers, setPrinters] = useState<Printer[]>([]);
  const [results, setResults] = useState<GlobalSearchResult[]>([]);
  const [printerId, setPrinterId] = useState("");
  const [search, setSearch] = useState("");
  const [classification, setClassification] = useState("");
  const [source, setSource] = useState("");
  const [level, setLevel] = useState("");
  const [startAt, setStartAt] = useState("");
  const [endAt, setEndAt] = useState("");
  const [limit, setLimit] = useState(100);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const sortedPrinters = useMemo(() => [...printers].sort((a, b) => a.name.localeCompare(b.name)), [printers]);

  const filters = {
    printer_id: printerId ? Number(printerId) : undefined,
    search,
    classification,
    source,
    level,
    start_at: startAt || undefined,
    end_at: endAt || undefined,
    limit
  };

  async function runSearch() {
    setIsLoading(true);
    setError(null);
    try {
      setResults(await globalSearch(filters));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    listPrinters()
      .then(setPrinters)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load printers"));
    void runSearch();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runSearch();
  }

  function handleExport() {
    window.open(exportUrl("/exports/search.txt", filters), "_blank");
  }

  return (
    <section className="page">
      <header>
        <p className="eyebrow">Search</p>
        <h2>Global console search</h2>
      </header>

      <div className="panel">
        <form className="filter-row search-filter-row" onSubmit={handleSubmit}>
          <select value={printerId} onChange={(event) => setPrinterId(event.target.value)}>
            <option value="">All printers</option>
            {sortedPrinters.map((printer) => (
              <option key={printer.id} value={printer.id}>
                {printer.name}
              </option>
            ))}
          </select>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search text" />
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
          <input type="datetime-local" value={startAt} onChange={(event) => setStartAt(event.target.value)} />
          <input type="datetime-local" value={endAt} onChange={(event) => setEndAt(event.target.value)} />
          <select value={limit} onChange={(event) => setLimit(Number(event.target.value))}>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={250}>250</option>
            <option value={500}>500</option>
          </select>
          <button type="submit" disabled={isLoading}>
            {isLoading ? "Searching" : "Search"}
          </button>
          <button type="button" className="secondary-button" onClick={handleExport}>
            Export TXT
          </button>
        </form>
        {error && <p className="error-text">{error}</p>}
      </div>

      <div className="panel table-panel">
        <div className="panel-heading">
          <h3>Results</h3>
          <span className="pill">{results.length}</span>
        </div>
        {results.length === 0 && <p>No matching entries.</p>}
        {results.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Collection</th>
                  <th>Printer</th>
                  <th>Level</th>
                  <th>Source</th>
                  <th>Classification</th>
                  <th>Message</th>
                </tr>
              </thead>
              <tbody>
                {results.map((result) => (
                  <tr key={`${result.collection}-${result.id}`}>
                    <td>{formatLocalDateTime(result.captured_at)}</td>
                    <td>{result.collection}</td>
                    <td>{result.printer_name ?? result.printer_id}</td>
                    <td>
                      <span className={`pill level-${result.level}`}>{result.level}</span>
                    </td>
                    <td>{result.source}</td>
                    <td>{result.classification}</td>
                    <td className="message-cell">{result.message}</td>
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
