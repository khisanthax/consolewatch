import { Link, Route, Routes } from "react-router-dom";

import ConsoleHistoryPage from "./pages/ConsoleHistoryPage";
import DashboardPage from "./pages/DashboardPage";
import LiveConsolePage from "./pages/LiveConsolePage";
import ManualSessionsPage from "./pages/ManualSessionsPage";
import PreservedCapturesPage from "./pages/PreservedCapturesPage";
import PrintersPage from "./pages/PrintersPage";
import SearchPage from "./pages/SearchPage";
import SettingsPage from "./pages/SettingsPage";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/printers", label: "Printers" },
  { to: "/live", label: "Live Console" },
  { to: "/history", label: "Console History" },
  { to: "/sessions", label: "Manual Sessions" },
  { to: "/captures", label: "Incident Captures" },
  { to: "/search", label: "Search" },
  { to: "/settings", label: "Settings" }
];

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">ConsoleWatch</p>
          <h1>Diagnostic Console Memory</h1>
        </div>
        <nav>
          {navItems.map((item) => (
            <Link key={item.to} to={item.to}>
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/printers" element={<PrintersPage />} />
          <Route path="/live" element={<LiveConsolePage />} />
          <Route path="/history" element={<ConsoleHistoryPage />} />
          <Route path="/sessions" element={<ManualSessionsPage />} />
          <Route path="/captures" element={<PreservedCapturesPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
