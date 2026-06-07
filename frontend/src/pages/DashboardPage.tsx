import HealthStatus from "../components/HealthStatus";

export default function DashboardPage() {
  return (
    <section className="page">
      <header>
        <p className="eyebrow">Dashboard</p>
        <h2>Printer console history</h2>
      </header>
      <div className="status-grid">
        <HealthStatus />
        <div className="panel">
          <h3>Current slice</h3>
          <p>Phase 0 scaffold. Printer profiles, ingestion, sessions, preservation, and search are planned next.</p>
        </div>
      </div>
    </section>
  );
}
