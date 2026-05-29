// Source: backend/app/schemas/media.py and backend/app/models/enums.py

import type { Timestamped } from "./common";
import type { SignalType } from "./signal";

export const MEDIA_SOURCE_TYPES = [
  "youtube",
  "podcast",
  "earnings_call",
  "webinar",
  "conference",
  "interview",
  "other",
] as const;
export type MediaSourceType = (typeof MEDIA_SOURCE_TYPES)[number];

export const MEDIA_SCAN_MODES = ["mock", "live"] as const;
export type MediaScanMode = (typeof MEDIA_SCAN_MODES)[number];

// Durable pipeline stages, in execution order (mirrors backend MediaScanStage).
export const MEDIA_SCAN_STAGES = [
  "queued",
  "discover_sources",
  "rank_sources",
  "resolve_media",
  "hash_media",
  "transcribe",
  "scrub_transcript",
  "extract_signals",
  "write_memory",
  "score_account",
  "notify",
  "completed",
  "failed",
] as const;
export type MediaScanStage = (typeof MEDIA_SCAN_STAGES)[number];

// Stages shown in the progress stepper (excludes queued/terminal states).
export const MEDIA_SCAN_STAGES_ORDERED: MediaScanStage[] = [
  "discover_sources",
  "rank_sources",
  "resolve_media",
  "hash_media",
  "transcribe",
  "scrub_transcript",
  "extract_signals",
  "write_memory",
  "score_account",
  "notify",
];

export const MEDIA_TERMINAL_STAGES: ReadonlySet<MediaScanStage> = new Set([
  "completed",
  "failed",
]);

export const MEDIA_SOURCE_STATUSES = [
  "discovered",
  "ranked",
  "selected",
  "skipped",
  "resolved",
  "transcribed",
  "extracted",
  "failed",
] as const;
export type MediaSourceStatus = (typeof MEDIA_SOURCE_STATUSES)[number];

export const PRIVACY_STATUSES = ["clean", "scrubbed", "sensitive_blocked"] as const;
export type PrivacyStatus = (typeof PRIVACY_STATUSES)[number];

export const TRANSCRIPT_PROVIDERS = [
  "speechmatics",
  "captions",
  "existing_transcript",
  "mock",
] as const;
export type TranscriptProvider = (typeof TRANSCRIPT_PROVIDERS)[number];

export const MEDIA_SCAN_EVENT_TYPES = [
  "stage_started",
  "stage_completed",
  "stage_skipped",
  "bright_data_call",
  "featherless_call",
  "aiml_call",
  "speechmatics_call",
  "cache_hit",
  "memory_write",
  "pii_redaction",
  "notification",
  "warning",
  "error",
  "info",
] as const;
export type MediaScanEventType = (typeof MEDIA_SCAN_EVENT_TYPES)[number];

export type MediaScanCounts = {
  sources_discovered: number;
  sources_selected: number;
  transcripts: number;
  cache_hits: number;
  conversation_signals: number;
  memory_writes: number;
};

export type MediaScanRead = Timestamped & {
  id: string;
  account_id: string;
  mode: MediaScanMode;
  status: MediaScanStage;
  current_stage: MediaScanStage;
  progress_percent: number;
  attempt_count: number;
  last_error?: string | null;
  score_delta?: number | null;
  stage_state_json?: Record<string, unknown> | null;
  started_at?: string | null;
  completed_at?: string | null;
  counts?: MediaScanCounts;
};

export type MediaScanCreateRequest = {
  mode?: MediaScanMode;
  max_sources?: number;
  force_refresh?: boolean;
};

export type MediaScanCreateResponse = {
  media_scan_id: string;
  status: MediaScanStage;
  mode: MediaScanMode;
};

export type MediaScanEventRead = {
  id: string;
  media_scan_job_id: string;
  sequence: number;
  stage?: MediaScanStage | null;
  event_type: MediaScanEventType;
  message: string;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
};

export type MediaScanEventList = {
  items: MediaScanEventRead[];
  total: number;
};

export type MediaSourceRead = Timestamped & {
  id: string;
  account_id: string;
  media_scan_job_id?: string | null;
  media_asset_id?: string | null;
  source_url: string;
  source_type: MediaSourceType;
  title?: string | null;
  description?: string | null;
  publisher?: string | null;
  speaker_names_json?: string[] | null;
  published_at?: string | null;
  duration_seconds?: number | null;
  transcript_available: boolean;
  discovery_query?: string | null;
  rank_score?: number | null;
  rank_reason?: string | null;
  status: MediaSourceStatus;
  metadata_json?: Record<string, unknown> | null;
};

export type ConversationSignalRead = Timestamped & {
  id: string;
  media_scan_job_id: string;
  account_id: string;
  media_source_id?: string | null;
  media_asset_id?: string | null;
  transcript_id?: string | null;
  signal_type: SignalType;
  title: string;
  summary?: string | null;
  fact_text?: string | null;
  inference_text?: string | null;
  recommended_action?: string | null;
  source_url: string;
  quote_text?: string | null;
  quote_start_seconds?: number | null;
  quote_end_seconds?: number | null;
  speaker_label?: string | null;
  observed_at?: string | null;
  confidence: number;
  recency_days?: number | null;
  privacy_status: PrivacyStatus;
  metadata_json?: Record<string, unknown> | null;
};

export type ConversationSignalList = {
  items: ConversationSignalRead[];
  total: number;
};

export type TranscriptSegment = {
  start?: number | null;
  end?: number | null;
  speaker?: string | null;
  text?: string | null;
  privacy_status?: string | null;
};

export type TranscriptRead = Timestamped & {
  id: string;
  media_asset_id: string;
  provider: TranscriptProvider;
  language?: string | null;
  scrubbed_text?: string | null;
  segments_json?: TranscriptSegment[] | null;
  confidence?: number | null;
  pii_status: PrivacyStatus;
  pii_findings_json?: Record<string, number> | null;
};
