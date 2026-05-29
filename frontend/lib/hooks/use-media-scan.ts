"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { mediaApi } from "@/lib/api";
import {
  MEDIA_TERMINAL_STAGES,
  type MediaScanCreateRequest,
  type MediaScanRead,
} from "@/lib/types";

const POLL_INTERVAL_MS = 1500;

export function useMediaScanStatus(scanId: string | null | undefined) {
  return useQuery({
    queryKey: ["media-scan", scanId],
    queryFn: ({ signal }) => mediaApi.getMediaScan(scanId!, signal),
    enabled: Boolean(scanId),
    refetchInterval: (query) => {
      const data = query.state.data as MediaScanRead | undefined;
      if (!data) return POLL_INTERVAL_MS;
      if (MEDIA_TERMINAL_STAGES.has(data.status)) return false;
      return POLL_INTERVAL_MS;
    },
  });
}

export function useMediaScanEvents(
  scanId: string | null | undefined,
  enabled = true,
) {
  return useQuery({
    queryKey: ["media-scan-events", scanId],
    queryFn: ({ signal }) => mediaApi.getMediaScanEvents(scanId!, 0, signal),
    enabled: Boolean(scanId) && enabled,
    refetchInterval: enabled ? POLL_INTERVAL_MS : false,
  });
}

export function useAccountMediaSources(accountId: string | null | undefined, enabled = true) {
  return useQuery({
    queryKey: ["media-sources", accountId],
    queryFn: ({ signal }) => mediaApi.getAccountMediaSources(accountId!, signal),
    enabled: Boolean(accountId) && enabled,
  });
}

export function useAccountConversationSignals(
  accountId: string | null | undefined,
  enabled = true,
) {
  return useQuery({
    queryKey: ["conversation-signals", accountId],
    queryFn: ({ signal }) => mediaApi.getAccountConversationSignals(accountId!, signal),
    enabled: Boolean(accountId) && enabled,
  });
}

export function useStartMediaScan(accountId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body?: MediaScanCreateRequest) => mediaApi.createMediaScan(accountId, body),
    onSuccess: (data) => {
      toast.success("Media scan queued", {
        description:
          data.mode === "live"
            ? "Listening for public conversations"
            : "Mock media scan queued",
      });
      queryClient.invalidateQueries({ queryKey: ["account", accountId] });
    },
    onError: () => {
      toast.error("Could not start media scan");
    },
  });
}

export function useResumeMediaScan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (scanId: string) => mediaApi.resumeMediaScan(scanId),
    onSuccess: (data) => {
      toast.success("Resuming media scan");
      queryClient.invalidateQueries({ queryKey: ["media-scan", data.media_scan_id] });
    },
    onError: () => {
      toast.error("Could not resume media scan");
    },
  });
}
