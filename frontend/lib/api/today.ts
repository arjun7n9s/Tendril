import { api } from "./client";
import type { TodayFeedResponse } from "@/lib/types";

export function getTodayFeed(limit = 8, signal?: AbortSignal) {
  return api.get<TodayFeedResponse>("/api/v1/today", {
    params: { limit },
    signal,
  });
}
