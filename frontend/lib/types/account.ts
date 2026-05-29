// Source: backend/app/schemas/account.py and backend/app/models/enums.py

import type { Timestamped } from "./common";
import type { ScanRead } from "./scan";
import type { SignalRead } from "./signal";
import type { AccountScoreSnapshot, BriefRead, ScoreRead } from "./brief";

export const ACCOUNT_STATUSES = [
  "target",
  "customer",
  "former_customer",
  "competitor",
  "ignored",
] as const;

export type AccountStatus = (typeof ACCOUNT_STATUSES)[number];

export type AccountRead = Timestamped & {
  id: string;
  name: string;
  domain?: string | null;
  industry?: string | null;
  company_size?: string | null;
  region?: string | null;
  status: AccountStatus;
  metadata_json?: Record<string, unknown> | null;
};

export type AccountListResponse = {
  items: AccountRead[];
  total: number;
  limit: number;
  offset: number;
};

export type AccountDetailResponse = {
  account: AccountRead;
  latest_scan: ScanRead | null;
  latest_score: ScoreRead | null;
  latest_score_snapshot: AccountScoreSnapshot | null;
  latest_brief: BriefRead | null;
  recent_signals: SignalRead[];
};

export type AccountListFilters = {
  status?: AccountStatus;
  search?: string;
  sales_ready?: boolean;
  near_miss?: boolean;
  limit?: number;
  offset?: number;
};
