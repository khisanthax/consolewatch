import { useEffect, useState } from "react";

import { getHealth } from "../lib/api";
import { formatLocalDateTime } from "../lib/time";

type HealthState =
  | { status: "loading" }
  | { status: "ready"; app: string; environment: string; checkedAt: string }
  | { status: "error"; message: string };

export default function HealthStatus() {
  const [health, setHealth] = useState<HealthState>({ status: "loading" });

  useEffect(() => {
    getHealth()
      .then((result) => {
        setHealth({
          status: "ready",
          app: result.app,
          environment: result.environment,
          checkedAt: result.checked_at
        });
      })
      .catch((error: unknown) => {
        setHealth({
          status: "error",
          message: error instanceof Error ? error.message : "Unknown health check error"
        });
      });
  }, []);

  return (
    <div className="panel">
      <h3>Backend health</h3>
      {health.status === "loading" && <p>Checking API...</p>}
      {health.status === "error" && <p className="error-text">{health.message}</p>}
      {health.status === "ready" && (
        <dl>
          <div>
            <dt>App</dt>
            <dd>{health.app}</dd>
          </div>
          <div>
            <dt>Environment</dt>
            <dd>{health.environment}</dd>
          </div>
          <div>
            <dt>Checked</dt>
            <dd>{formatLocalDateTime(health.checkedAt)}</dd>
          </div>
        </dl>
      )}
    </div>
  );
}
