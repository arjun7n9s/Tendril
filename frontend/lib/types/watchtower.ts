// Source: backend/app/schemas/watchtower.py

import type { Timestamped } from "./common";
import type { MediaScanMode } from "./media";

export type AccountWatchRead = Timestamped & {
  id: string;
  account_id: string;
  enabled: boolean;
  mode: MediaScanMode;
  interval_seconds: number;
  last_scanned_at?: string | null;
  next_due_at?: string | null;
  last_media_scan_job_id?: string | null;
  consecutive_failures: number;
  last_error?: string | null;
};

export type WatchUpsertRequest = {
  enabled: boolean;
  mode?: MediaScanMode;
  interval_seconds?: number;
};

export type WatchListResponse = {
  items: AccountWatchRead[];
  total: number;
  watchtower_enabled: boolean;
};
