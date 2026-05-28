// Source: backend/app/schemas/scan.py and backend/app/models/enums.py

import type { Timestamped } from "./common";

export const SCAN_TYPES = [
  "account_watchtower",
  "champion_mobility",
  "lookalike_discovery",
] as const;
export type ScanType = (typeof SCAN_TYPES)[number];

export const SCAN_STATUSES = [
  "queued",
  "discovering",
  "scraping",
  "extracting",
  "graphing",
  "scoring",
  "briefing",
  "completed",
  "failed",
] as const;
export type ScanStatus = (typeof SCAN_STATUSES)[number];

export const NON_TERMINAL_SCAN_STATUSES: ReadonlySet<ScanStatus> = new Set([
  "queued",
  "discovering",
  "scraping",
  "extracting",
  "graphing",
  "scoring",
  "briefing",
]);

export const TERMINAL_SCAN_STATUSES: ReadonlySet<ScanStatus> = new Set(["completed", "failed"]);

export const SCAN_PHASES_ORDERED: ScanStatus[] = [
  "queued",
  "discovering",
  "scraping",
  "extracting",
  "graphing",
  "scoring",
  "briefing",
  "completed",
];

export const SCAN_MODES = ["mock", "live", "cached"] as const;
export type ScanMode = (typeof SCAN_MODES)[number];

export const SCAN_EVENT_TYPES = [
  "phase_started",
  "phase_completed",
  "bright_data_call",
  "bright_data_call_replayed",
  "aiml_call",
  "aiml_call_replayed",
  "memory_write",
  "memory_write_replayed",
  "warning",
  "error",
  "info",
] as const;
export type ScanEventType = (typeof SCAN_EVENT_TYPES)[number];

export type ScanCounts = {
  discovered: number;
  selected: number;
  fetched: number;
  failed: number;
  signals: number;
  bright_data_calls: number;
  aiml_calls: number;
  memory_writes: number;
};

export type ScanRead = Timestamped & {
  id: string;
  account_id: string;
  scan_type: ScanType;
  status: ScanStatus;
  mode: ScanMode;
  progress_percent: number;
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  counts?: ScanCounts;
};

export type ScanCreateRequest = {
  scan_type?: ScanType;
  mode?: ScanMode;
  max_sources?: number;
  force_refresh?: boolean;
};

export type ScanCreateResponse = {
  scan_id: string;
  status: ScanStatus;
  mode: ScanMode;
};

export type ScanEventRead = {
  id: string;
  scan_id: string;
  sequence: number;
  phase?: ScanStatus | null;
  event_type: ScanEventType;
  message: string;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
};

export type ScanEventList = {
  items: ScanEventRead[];
  total: number;
};
