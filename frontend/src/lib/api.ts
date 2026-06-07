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
