"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { watchtowerApi } from "@/lib/api";
import type { WatchUpsertRequest } from "@/lib/types";

export function useAccountWatch(accountId: string | null | undefined) {
  return useQuery({
    queryKey: ["watch", accountId],
    queryFn: ({ signal }) => watchtowerApi.getWatch(accountId!, signal),
    enabled: Boolean(accountId),
  });
}

export function useUpsertWatch(accountId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: WatchUpsertRequest) => watchtowerApi.upsertWatch(accountId, body),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["watch", accountId] });
      toast.success(data.enabled ? "Watching this account" : "Watch paused", {
        description: data.enabled
          ? "Tendril will re-scan for new public conversations on a schedule."
          : undefined,
      });
    },
    onError: () => {
      toast.error("Could not update watch");
    },
  });
}
