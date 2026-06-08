import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  createPrinter,
  deletePrinter,
  listPrinters,
  Printer,
  PrinterPayload,
  updatePrinter
} from "../lib/api";
import { formatLocalDateTime, formatOptionalLocalDateTime } from "../lib/time";

type PrinterFormState = {
  name: string;
  base_url: string;
  api_key: string;
  is_enabled: boolean;
  console_watch_enabled: boolean;
  retention_hours: number;
};

const emptyForm: PrinterFormState = {
  name: "",
  base_url: "",
  api_key: "",
  is_enabled: true,
  console_watch_enabled: false,
  retention_hours: 8
};

const retentionOptions = [
  { value: 4, label: "4 hours" },
  { value: 8, label: "8 hours" },
  { value: 12, label: "12 hours" },
  { value: 24, label: "1 day" },
  { value: 48, label: "2 days" },
  { value: 72, label: "3 days" },
  { value: 168, label: "1 week" },
  { value: 336, label: "2 weeks" },
  { value: 720, label: "1 month" }
];

function formatRetention(hours: number) {
  const option = retentionOptions.find((item) => item.value === hours);
  if (option) {
    return option.label;
  }
  return hours < 24 ? `${hours}h` : `${Math.round(hours / 24)} days`;
}

function formFromPrinter(printer: Printer): PrinterFormState {
  return {
    name: printer.name,
    base_url: printer.base_url,
    api_key: "",
    is_enabled: printer.is_enabled,
    console_watch_enabled: printer.console_watch_enabled,
    retention_hours: printer.retention_hours
  };
}

function payloadFromForm(form: PrinterFormState, includeBlankApiKey: boolean): PrinterPayload {
  const payload: PrinterPayload = {
    name: form.name.trim(),
    base_url: form.base_url.trim(),
    is_enabled: form.is_enabled,
    console_watch_enabled: form.console_watch_enabled,
    retention_hours: form.retention_hours
  };

  if (includeBlankApiKey || form.api_key.trim()) {
    payload.api_key = form.api_key.trim() || null;
  }

  return payload;
}

export default function PrintersPage() {
  const [printers, setPrinters] = useState<Printer[]>([]);
  const [form, setForm] = useState<PrinterFormState>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sortedPrinters = useMemo(
    () => [...printers].sort((a, b) => a.name.localeCompare(b.name)),
    [printers]
  );

  async function refreshPrinters() {
    setIsLoading(true);
    setError(null);
    try {
      setPrinters(await listPrinters());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load printers");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void refreshPrinters();
  }, []);

  function resetForm() {
    setForm(emptyForm);
    setEditingId(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);

    try {
      if (editingId === null) {
        await createPrinter(payloadFromForm(form, true));
      } else {
        const payload = payloadFromForm(form, false);
        await updatePrinter(editingId, payload);
      }
      resetForm();
      await refreshPrinters();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save printer");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete(printer: Printer) {
    const confirmed = window.confirm(`Delete ${printer.name}? Console data for this printer will also be removed.`);
    if (!confirmed) {
      return;
    }

    setError(null);
    try {
      await deletePrinter(printer.id);
      if (editingId === printer.id) {
        resetForm();
      }
      await refreshPrinters();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete printer");
    }
  }

  return (
    <section className="page">
      <header>
        <p className="eyebrow">Printers</p>
        <h2>Printer profiles</h2>
      </header>

      <div className="stack-layout">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <h3>{editingId === null ? "Add printer" : "Edit printer"}</h3>
          <label>
            <span>Name</span>
            <input
              required
              maxLength={160}
              value={form.name}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              placeholder="Voron Trident"
            />
          </label>
          <label>
            <span>Moonraker URL</span>
            <input
              required
              type="url"
              value={form.base_url}
              onChange={(event) => setForm((current) => ({ ...current, base_url: event.target.value }))}
              placeholder="http://printer.local:7125"
            />
          </label>
          <label>
            <span>API key</span>
            <input
              type="password"
              value={form.api_key}
              onChange={(event) => setForm((current) => ({ ...current, api_key: event.target.value }))}
              placeholder={editingId === null ? "Optional" : "Leave blank to keep existing"}
            />
          </label>
          <label>
            <span>Retention</span>
            <select
              value={form.retention_hours}
              onChange={(event) =>
                setForm((current) => ({ ...current, retention_hours: Number(event.target.value) }))
              }
            >
              {retentionOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <div className="toggle-row">
            <label>
              <input
                type="checkbox"
                checked={form.is_enabled}
                onChange={(event) => setForm((current) => ({ ...current, is_enabled: event.target.checked }))}
              />
              <span>Enabled</span>
            </label>
            <label>
              <input
                type="checkbox"
                checked={form.console_watch_enabled}
                onChange={(event) =>
                  setForm((current) => ({ ...current, console_watch_enabled: event.target.checked }))
                }
              />
              <span>Continuous watch</span>
            </label>
          </div>
          <div className="button-row">
            <button type="submit" disabled={isSaving}>
              {isSaving ? "Saving" : editingId === null ? "Add Printer" : "Save Changes"}
            </button>
            {editingId !== null && (
              <button type="button" className="secondary-button" onClick={resetForm}>
                Cancel
              </button>
            )}
          </div>
          {error && <p className="error-text">{error}</p>}
        </form>

        <div className="panel table-panel">
          <div className="panel-heading">
            <h3>Saved printers</h3>
            <button type="button" className="secondary-button" onClick={() => void refreshPrinters()}>
              Refresh
            </button>
          </div>
          {isLoading && <p>Loading printers...</p>}
          {!isLoading && sortedPrinters.length === 0 && <p>No printer profiles saved yet.</p>}
          {!isLoading && sortedPrinters.length > 0 && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Moonraker</th>
                    <th>Status</th>
                    <th>Continuous watch</th>
                    <th>Updated</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedPrinters.map((printer) => (
                    <tr key={printer.id}>
                      <td>
                        <strong>{printer.name}</strong>
                        <small>Created {formatLocalDateTime(printer.created_at)}</small>
                      </td>
                      <td>{printer.base_url}</td>
                      <td>
                        <span className="pill">{printer.connection_status}</span>
                        <small>Last connected {formatOptionalLocalDateTime(printer.last_connected_at)}</small>
                      </td>
                      <td>{printer.console_watch_enabled ? formatRetention(printer.retention_hours) : "Off"}</td>
                      <td>{formatLocalDateTime(printer.updated_at)}</td>
                      <td>
                        <div className="row-actions">
                          <button
                            type="button"
                            className="secondary-button"
                            onClick={() => {
                              setEditingId(printer.id);
                              setForm(formFromPrinter(printer));
                            }}
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            className="danger-button"
                            onClick={() => void handleDelete(printer)}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
