/** Format a number of seconds as a mm:ss (or h:mm:ss) timecode. */
export function formatTimecode(seconds?: number | null): string {
  if (seconds === null || seconds === undefined || Number.isNaN(seconds)) return "--:--";
  const total = Math.max(0, Math.floor(seconds));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const mm = m.toString().padStart(2, "0");
  const ss = s.toString().padStart(2, "0");
  if (h > 0) return `${h}:${mm}:${ss}`;
  return `${mm}:${ss}`;
}

/** Format a duration in seconds as a human label, e.g. "44 min". */
export function formatDuration(seconds?: number | null): string {
  if (!seconds || seconds <= 0) return "—";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m ? `${h}h ${m}m` : `${h}h`;
}
