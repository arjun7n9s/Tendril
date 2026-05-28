// Source: backend/app/schemas/outreach.py and backend/app/models/enums.py

import type { Timestamped } from "./common";

export const OUTREACH_TONES = ["warm", "technical", "executive", "concise"] as const;
export type OutreachTone = (typeof OUTREACH_TONES)[number];

export const OUTREACH_STATUSES = [
  "pending_review",
  "approved",
  "rejected",
  "edited",
] as const;
export type OutreachStatus = (typeof OUTREACH_STATUSES)[number];

export type OutreachRead = Timestamped & {
  id: string;
  scan_id: string;
  account_id: string;
  person_id?: string | null;
  subject: string;
  body: string;
  tone: OutreachTone;
  status: OutreachStatus;
  guardrail_notes_json?: unknown[] | null;
  reviewer_feedback?: string | null;
};

export type OutreachList = {
  items: OutreachRead[];
  total: number;
};

export type OutreachReject = {
  feedback?: string;
};

export type OutreachPatch = {
  subject?: string;
  body?: string;
  tone?: OutreachTone;
};
