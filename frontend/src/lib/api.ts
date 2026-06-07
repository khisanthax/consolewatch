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
    if (value !== undefined && value !== null && value !== "") {
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
