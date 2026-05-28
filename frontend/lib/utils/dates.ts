import { formatDistanceToNowStrict, parseISO } from "date-fns";

export function formatRelative(value?: string | null, fallback = "—"): string {
  if (!value) return fallback;
  try {
    const date = typeof value === "string" ? parseISO(value) : new Date(value);
    if (Number.isNaN(date.getTime())) return fallback;
    return `${formatDistanceToNowStrict(date)} ago`;
  } catch {
    return fallback;
  }
}

export function formatAbsolute(value?: string | null): string {
  if (!value) return "—";
  try {
    const date = parseISO(value);
    if (Number.isNaN(date.getTime())) return "—";
    return new Intl.DateTimeFormat(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  } catch {
    return "—";
  }
}
