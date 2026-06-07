import { useEffect, useState } from "react";

import HealthStatus from "../components/HealthStatus";
import { getWatchStatus, listPrinters, Printer, WatchStatus } from "../lib/api";

export default function DashboardPage() {
  const [printers, setPrinters] = useState<Printer[]>([]);
  const [watchStatus, setWatchStatus] = useState<WatchStatus | null>(null);

  useEffect(() => {
    listPrinters()
      .then(setPrinters)
      .catch(() => setPrinters([]));
    getWatchStatus()
      .then(setWatchStatus)
      .catch(() => setWatchStatus(null));
  }, []);

  const watchEnabledCount = printers.filter((printer) => printer.console_watch_enabled).length;

  return (
    <section className="page">
      <header>
        <p className="eyebrow">Dashboard</p>
        <h2>Printer console history</h2>
      </header>
      <div className="status-grid">
        <HealthStatus />
        <div className="panel">
          <h3>Printer profiles</h3>
          <dl>
            <div>
              <dt>Saved</dt>
              <dd>{printers.length}</dd>
            </div>
            <div>
              <dt>Rolling watch enabled</dt>
              <dd>{watchEnabledCount}</dd>
            </div>
          </dl>
        </div>
        <div className="panel">
          <h3>Rolling watch</h3>
          <dl>
            <div>
              <dt>Background worker</dt>
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
        </div>
      </div>
    </section>
  );
}
