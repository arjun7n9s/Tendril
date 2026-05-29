// Source: backend/app/schemas/brief.py

import type { Timestamped } from "./common";

export type ScoreRead = Timestamped & {
  id: string;
  scan_id: string;
  account_id: string;
  fit_score: number;
  timing_score: number;
  relationship_score: number;
  evidence_score: number;
  total_score: number;
  sales_ready: boolean;
  score_reasoning_json?: Record<string, unknown> | null;
};

/**
 * Unified, modality-aware account score (web + media).
 * Source of the headline number; `conversation_delta` is the spoken-evidence
 * contribution when `source === "media_scan"`.
 */
export type AccountScoreSnapshot = {
  id: string;
  account_id: string;
  fit_score: number;
  timing_score: number;
  relationship_score: number;
  evidence_score: number;
  total_score: number;
  sales_ready: boolean;
  source: "web_scan" | "media_scan";
  conversation_delta?: number | null;
  reasoning_json?: Record<string, unknown> | null;
  created_at?: string | null;
};

export type BriefEvidenceItem = {
  text: string;
  url?: string;
  source?: string;
  evidence_id?: string;
} & Record<string, unknown>;

export type BriefRead = Timestamped & {
  id: string;
  scan_id: string;
  account_id: string;
  title: string;
  executive_summary?: string | null;
  why_now?: string | null;
  key_evidence_json?: BriefEvidenceItem[] | null;
  risks_json?: string[] | null;
  recommended_next_steps_json?: string[] | null;
};
