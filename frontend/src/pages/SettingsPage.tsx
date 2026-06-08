import { useEffect, useState } from "react";

import { Diagnostics, getDiagnostics } from "../lib/api";

function formatBytes(value: number | null): string {
  if (value === null) {
    return "Unavailable";
  }
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

export default function SettingsPage() {
  const [diagnostics, setDiagnostics] = useState<Diagnostics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDiagnostics()
      .then(setDiagnostics)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load diagnostics"));
  }, []);

  return (
    <section className="page">
      <header>
        <p className="eyebrow">Settings</p>
        <h2>Diagnostics and storage</h2>
      </header>

      {error && <div className="panel error-text">{error}</div>}

      <div className="status-grid">
        <div className="panel">
          <h3>Storage</h3>
          <dl>
            <div>
              <dt>Backend</dt>
              <dd>{diagnostics?.storage.database_backend ?? "Unknown"}</dd>
            </div>
            <div>
              <dt>SQLite path</dt>
              <dd>{diagnostics?.storage.sqlite_path ?? "Unavailable"}</dd>
            </div>
            <div>
              <dt>Exists</dt>
              <dd>{diagnostics?.storage.sqlite_exists ? "Yes" : "No"}</dd>
            </div>
            <div>
              <dt>Size</dt>
              <dd>{formatBytes(diagnostics?.storage.sqlite_size_bytes ?? null)}</dd>
            </div>
          </dl>
        </div>

        <div className="panel">
          <h3>Runtime</h3>
          <dl>
            <div>
              <dt>Environment</dt>
              <dd>{diagnostics?.runtime.environment ?? "Unknown"}</dd>
            </div>
            <div>
              <dt>Background watch</dt>
              <dd>{diagnostics?.runtime.background_watch_enabled ? "Enabled" : "Disabled"}</dd>
            </div>
            <div>
              <dt>Prune interval</dt>
              <dd>{diagnostics?.runtime.retention_prune_interval_seconds ?? 0}s</dd>
            </div>
            <div>
              <dt>Reconnect delay</dt>
              <dd>{diagnostics?.runtime.moonraker_reconnect_delay_seconds ?? 0}s</dd>
            </div>
          </dl>
        </div>

        <div className="panel">
          <h3>Record counts</h3>
          <dl>
            {Object.entries(diagnostics?.counts ?? {}).map(([key, value]) => (
              <div key={key}>
                <dt>{key}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>

      <div className="panel">
        <h3>Trigger rules</h3>
        <div className="pill-list">
          {(diagnostics?.trigger_classifications ?? []).map((classification) => (
            <span key={classification} className="pill">
              {classification}
            </span>
          ))}
        </div>
        <p>Boundary duplicate suppression: {diagnostics?.boundary_suppression_seconds ?? 0}s</p>
      </div>

      <div className="panel">
        <h3>Deployment notes</h3>
        <ul className="plain-list">
          <li>Back up the SQLite database from the persistent Docker volume or the host folder mounted to /data.</li>
          <li>Removing the Docker volume removes all ConsoleWatch data.</li>
          <li>Redeployed frontend assets should refresh cleanly because index.html is served with no-cache headers.</li>
          <li>ConsoleWatch is designed for a trusted LAN and should not be exposed directly to the public internet.</li>
          {(diagnostics?.notes ?? []).map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
