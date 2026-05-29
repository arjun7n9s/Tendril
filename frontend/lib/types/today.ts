// Source: backend/app/schemas/today.py

export type TodayFeedItem = {
  account_id: string;
  account_name: string;
  domain?: string | null;
  total_score: number;
  sales_ready: boolean;
  source: "web_scan" | "media_scan";
  conversation_delta?: number | null;
  why_now: string;
  reason_tags: string[];
  updated_at: string;
};

export type TodayFeedResponse = {
  items: TodayFeedItem[];
  total: number;
  generated_at: string;
};
