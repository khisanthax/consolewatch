import { useEffect, useState } from "react";

import HealthStatus from "../components/HealthStatus";
import { listPrinters, Printer } from "../lib/api";

export default function DashboardPage() {
  const [printers, setPrinters] = useState<Printer[]>([]);

  useEffect(() => {
    listPrinters()
      .then(setPrinters)
      .catch(() => setPrinters([]));
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
      </div>
    </section>
  );
}
