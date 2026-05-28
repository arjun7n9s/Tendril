"use client";

import { useQuery } from "@tanstack/react-query";

import { healthApi } from "@/lib/api";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => healthApi.getHealth(signal),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}
