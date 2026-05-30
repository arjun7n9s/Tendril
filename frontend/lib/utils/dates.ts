import { formatDistanceToNowStrict, parseISO } from "date-fns";

const FALLBACK_DASH = "-";

export function parseBackendDate(value: string): Date {
  const trimmed = value.trim();
  // FastAPI/SQLAlchemy can serialize UTC datetimes without a timezone suffix.
  // Browsers parse those as local time, which made fresh live-scan events look
  // around 5-6 hours old in IST. Treat timezone-less ISO timestamps as UTC.
  // Date-only values (YYYY-MM-DD) are already parsed as UTC midnight by
  // parseISO, so we only append Z when there's a time component.
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(trimmed);
  const hasTime = trimmed.includes("T");
  return parseISO(hasTime && !hasTimezone ? `${trimmed}Z` : trimmed);
}

export function formatRelative(value?: string | null, fallback = FALLBACK_DASH): string {
  if (!value) return fallback;
  try {
    const date = typeof value === "string" ? parseBackendDate(value) : new Date(value);
    if (Number.isNaN(date.getTime())) return fallback;
    return `${formatDistanceToNowStrict(date)} ago`;
  } catch {
    return fallback;
  }
}

export function formatAbsolute(value?: string | null): string {
  if (!value) return FALLBACK_DASH;
  try {
    const date = parseBackendDate(value);
    if (Number.isNaN(date.getTime())) return FALLBACK_DASH;
    return new Intl.DateTimeFormat(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  } catch {
    return FALLBACK_DASH;
  }
}
