const fallbackTimeZone = "America/New_York";

export function formatLocalDateTime(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value);
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone || fallbackTimeZone;

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
    timeZone
  }).format(date);
}

export function formatOptionalLocalDateTime(value: string | null): string {
  return value ? formatLocalDateTime(value) : "Never";
}
