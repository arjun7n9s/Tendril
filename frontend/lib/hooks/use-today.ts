"use client";

import { useQuery } from "@tanstack/react-query";

import { todayApi } from "@/lib/api";

export function useTodayFeed(limit = 8) {
  return useQuery({
    queryKey: ["today", limit],
    queryFn: ({ signal }) => todayApi.getTodayFeed(limit, signal),
    refetchInterval: 30_000,
  });
}
