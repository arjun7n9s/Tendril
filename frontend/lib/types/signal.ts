// Source: backend/app/schemas/signal.py and backend/app/models/enums.py

import type { Timestamped } from "./common";

export const SIGNAL_TYPES = [
  "hiring",
  "tech_stack",
  "migration",
  "funding",
  "product_launch",
  "leadership_change",
  "competitor_mention",
  "champion_move",
  "market_event",
  "other",
] as const;
export type SignalType = (typeof SIGNAL_TYPES)[number];

export const SOURCE_TYPES = [
  "company_site",
  "careers",
  "blog",
  "news",
  "github",
  "docs",
  "serp_result",
  "review",
  "public_profile",
  "other",
] as const;
export type SourceType = (typeof SOURCE_TYPES)[number];

export const FETCH_METHODS = [
  "brightdata_mcp",
  "serp_api",
  "unlocker",
  "browser_api",
  "web_scraper_api",
  "mock",
  "cached",
] as const;
export type FetchMethod = (typeof FETCH_METHODS)[number];

export const FETCH_STATUSES = ["success", "failed", "skipped"] as const;
export type FetchStatus = (typeof FETCH_STATUSES)[number];

export type SignalRead = Timestamped & {
  id: string;
  scan_id: string;
  account_id: string;
  person_id?: string | null;
  signal_type: SignalType;
  title: string;
  summary?: string | null;
  fact_text?: string | null;
  inference_text?: string | null;
  recommended_action?: string | null;
  evidence_url: string;
  evidence_document_id?: string | null;
  observed_at?: string | null;
  confidence: number;
  recency_days?: number | null;
  metadata_json?: Record<string, unknown> | null;
};

export type SignalList = {
  items: SignalRead[];
  total: number;
};

export type SourceRead = Timestamped & {
  id: string;
  scan_id: string;
  account_id: string;
  url: string;
  source_type: SourceType;
  discovery_query?: string | null;
  rank: number;
  selected_for_scrape: boolean;
};

export type EvidenceRead = {
  id: string;
  scan_id: string;
  source_id?: string | null;
  account_id: string;
  url: string;
  title?: string | null;
  content_markdown?: string | null;
  content_hash?: string | null;
  fetched_at?: string | null;
  fetch_status: FetchStatus;
  fetch_method: FetchMethod;
  http_status?: number | null;
  metadata_json?: Record<string, unknown> | null;
};
