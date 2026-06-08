export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers
    },
    ...options
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function getHealth() {
  return requestJson<{
    status: string;
    app: string;
    environment: string;
    checked_at: string;
  }>("/health");
}

export function getDiagnostics() {
  return requestJson<Diagnostics>("/diagnostics");
}

export type Printer = {
  id: number;
  name: string;
  base_url: string;
  is_enabled: boolean;
  console_watch_enabled: boolean;
  retention_hours: number;
  connection_status: string;
  last_connected_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
};

export type PrinterPayload = {
  name: string;
  base_url: string;
  api_key?: string | null;
  is_enabled: boolean;
  console_watch_enabled: boolean;
  retention_hours: number;
};

export type ConsoleEntry = {
  id: number;
  printer_id: number;
  captured_at: string;
  source: string;
  level: string;
  message: string;
  raw_payload_json: string | null;
  classification: string;
  event_type: string | null;
  print_state: string | null;
  filename: string | null;
  restart_boundary_id: number | null;
  boundary_type: string | null;
  created_at: string;
};

export type ConsoleEntryFilters = {
  printer_id?: number;
  search?: string;
  classification?: string;
  source?: string;
  level?: string;
  limit?: number;
};

export type WatchStatus = {
  active_printer_ids: number[];
  task_count: number;
  background_watch_enabled: boolean;
  watched_printer_count: number;
};

export type RetentionPruneResult = {
  deleted_by_printer: Record<string, number>;
  deleted_total: number;
};

export type ManualSessionEntry = {
  id: number;
  session_id: number;
  original_console_entry_id: number | null;
  captured_at: string;
  source: string;
  level: string;
  message: string;
  raw_payload_json: string | null;
  classification: string;
  event_type: string | null;
  print_state: string | null;
  filename: string | null;
  created_at: string;
};

export type ManualSession = {
  id: number;
  printer_id: number;
  printer_name: string | null;
  label: string;
  notes: string | null;
  status: string;
  started_at: string;
  ended_at: string | null;
  saved: boolean;
  stop_reason: string | null;
  created_at: string;
  updated_at: string;
  entry_count: number;
};

export type ManualSessionDetail = ManualSession & {
  entries: ManualSessionEntry[];
};

export type ManualSessionFilters = {
  search?: string;
  classification?: string;
  source?: string;
  level?: string;
  limit?: number;
};

export type PreservedEntry = {
  id: number;
  preserved_capture_id: number;
  original_console_entry_id: number | null;
  captured_at: string;
  source: string;
  level: string;
  message: string;
  raw_payload_json: string | null;
  classification: string;
  event_type: string | null;
  print_state: string | null;
  filename: string | null;
  is_trigger_entry: boolean;
  boundary_type: string | null;
  created_at: string;
};

export type DetectedEvent = {
  id: number;
  printer_id: number;
  captured_at: string;
  event_type: string;
  severity: string;
  message: string;
  related_capture_id: number | null;
  related_session_id: number | null;
  restart_boundary_id: number | null;
  created_at: string;
};

export type PreservedCapture = {
  id: number;
  printer_id: number;
  printer_name: string | null;
  trigger_type: string;
  trigger_reason: string;
  trigger_message: string;
  triggered_at: string;
  started_at: string;
  ended_at: string;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
  entry_count: number;
};

export type PreservedCaptureDetail = PreservedCapture & {
  entries: PreservedEntry[];
  detected_events: DetectedEvent[];
};

export type GlobalSearchResult = {
  collection: string;
  id: number;
  parent_id: number | null;
  printer_id: number;
  printer_name: string | null;
  captured_at: string;
  source: string;
  level: string;
  classification: string;
  message: string;
};

export type GlobalSearchFilters = {
  printer_id?: number;
  search?: string;
  classification?: string;
  source?: string;
  level?: string;
  start_at?: string;
  end_at?: string;
  limit?: number;
};

export type Diagnostics = {
  counts: Record<string, number>;
  storage: {
    database_backend: string;
    sqlite_path: string | null;
    sqlite_exists: boolean;
    sqlite_size_bytes: number | null;
  };
  runtime: {
    app_name: string;
    environment: string;
    background_watch_enabled: boolean;
    watch_manager_interval_seconds: number;
    retention_prune_interval_seconds: number;
    moonraker_reconnect_delay_seconds: number;
  };
  trigger_classifications: string[];
  trigger_message_markers: string[];
  boundary_suppression_seconds: number;
  notes: string[];
};

export function listPrinters() {
  return requestJson<Printer[]>("/printers");
}

export function createPrinter(payload: PrinterPayload) {
  return requestJson<Printer>("/printers", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updatePrinter(id: number, payload: Partial<PrinterPayload>) {
  return requestJson<Printer>(`/printers/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function deletePrinter(id: number) {
  return requestJson<void>(`/printers/${id}`, {
    method: "DELETE"
  });
}

export function listConsoleEntries(filters: ConsoleEntryFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      params.set(key, String(value));
    }
  });
  const query = params.toString();
  return requestJson<ConsoleEntry[]>(`/console-entries${query ? `?${query}` : ""}`);
}

export function ingestMoonrakerNotification(printerId: number, payload: unknown) {
  return requestJson<{ entries_created: number; entries: ConsoleEntry[] }>(
    `/console-entries/moonraker-notification?printer_id=${printerId}`,
    {
      method: "POST",
      body: JSON.stringify(payload)
    }
  );
}

export function getWatchStatus() {
  return requestJson<WatchStatus>("/watch/status");
}

export function pruneWatchEntries() {
  return requestJson<RetentionPruneResult>("/watch/prune", {
    method: "POST"
  });
}

export function listManualSessions(printerId?: number) {
  const query = printerId ? `?printer_id=${printerId}` : "";
  return requestJson<ManualSession[]>(`/sessions${query}`);
}

export function startManualSession(payload: { printer_id: number; label: string; notes?: string | null }) {
  return requestJson<ManualSession>("/sessions", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getManualSession(id: number, filters: ManualSessionFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  });
  const query = params.toString();
  return requestJson<ManualSessionDetail>(`/sessions/${id}${query ? `?${query}` : ""}`);
}

export function stopManualSession(id: number, stopReason = "manual") {
  return requestJson<ManualSession>(`/sessions/${id}/stop`, {
    method: "POST",
    body: JSON.stringify({ stop_reason: stopReason })
  });
}

export function saveManualSession(id: number) {
  return requestJson<ManualSession>(`/sessions/${id}/save`, {
    method: "POST"
  });
}

export function discardManualSession(id: number) {
  return requestJson<void>(`/sessions/${id}`, {
    method: "DELETE"
  });
}

export function listPreservedCaptures(filters: { printer_id?: number; limit?: number } = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      params.set(key, String(value));
    }
  });
  const query = params.toString();
  return requestJson<PreservedCapture[]>(`/preserved-captures${query ? `?${query}` : ""}`);
}

export function getPreservedCapture(id: number, filters: ManualSessionFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  });
  const query = params.toString();
  return requestJson<PreservedCaptureDetail>(`/preserved-captures/${id}${query ? `?${query}` : ""}`);
}

export function globalSearch(filters: GlobalSearchFilters = {}) {
  const query = queryString(filters);
  return requestJson<GlobalSearchResult[]>(`/search${query ? `?${query}` : ""}`);
}

export function exportUrl(path: string, filters: Record<string, string | number | undefined | null> = {}) {
  const query = queryString(filters);
  return `${API_BASE_URL}${path}${query ? `?${query}` : ""}`;
}

function queryString(filters: Record<string, string | number | undefined | null>) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  });
  return params.toString();
}
