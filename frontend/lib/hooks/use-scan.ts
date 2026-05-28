"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { scansApi } from "@/lib/api";
import { COPY } from "@/lib/copy";
import {
  type ScanCreateRequest,
  type ScanRead,
  TERMINAL_SCAN_STATUSES,
} from "@/lib/types";

const POLL_INTERVAL_MS = 1500;

/**
 * Polls a single scan until it reaches a terminal status.
 *
 * Decision sourced from kiro/kiro-frontend-requirements-checklist.md F:
 *   - refetchInterval 1500ms while non-terminal,
 *   - stop polling on completed | failed,
 *   - 3s grace before any error toast (handled at the consumer).
 */
export function useScanStatus(scanId: string | null | undefined) {
  return useQuery({
    queryKey: ["scan", scanId],
    queryFn: ({ signal }) => scansApi.getScan(scanId!, signal),
    enabled: Boolean(scanId),
    refetchInterval: (query) => {
      const data = query.state.data as ScanRead | undefined;
      if (!data) return POLL_INTERVAL_MS;
      if (TERMINAL_SCAN_STATUSES.has(data.status)) return false;
      return POLL_INTERVAL_MS;
    },
  });
}

export function useScanEvents(
  scanId: string | null | undefined,
  afterSequence = 0,
  enabled = true,
) {
  return useQuery({
    queryKey: ["scan-events", scanId, afterSequence],
    queryFn: ({ signal }) => scansApi.getScanEvents(scanId!, afterSequence, signal),
    enabled: Boolean(scanId) && enabled,
    refetchInterval: enabled ? POLL_INTERVAL_MS : false,
  });
}

export function useScanSources(scanId: string | null | undefined, enabled = true) {
  return useQuery({
    queryKey: ["scan-sources", scanId],
    queryFn: ({ signal }) => scansApi.getScanSources(scanId!, signal),
    enabled: Boolean(scanId) && enabled,
    refetchInterval: enabled ? POLL_INTERVAL_MS : false,
  });
}

export function useScanEvidence(scanId: string | null | undefined, enabled = true) {
  return useQuery({
    queryKey: ["scan-evidence", scanId],
    queryFn: ({ signal }) => scansApi.getScanEvidence(scanId!, signal),
    enabled: Boolean(scanId) && enabled,
  });
}

/**
 * Mutation that kicks off a scan for an account.
 *
 * The backend coerces `mode=live` to `mock` when Bright Data is not
 * configured, which is fine; the resulting ScanRead.mode is the
 * source of truth and the live-scan panel will reflect it.
 */
export function useStartScan(accountId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body?: ScanCreateRequest) => scansApi.createScan(accountId, body),
    onSuccess: (data) => {
      toast.success(COPY.scan.queuedToast, {
        description:
          data.mode === "live"
            ? "Bright Data live scan queued"
            : "Mock scan queued — backend not in live mode",
      });
      // Re-fetch the account so the latest_scan reference updates and
      // the panel can pick up the new scan id.
      queryClient.invalidateQueries({ queryKey: ["account", accountId] });
    },
    onError: () => {
      toast.error("Could not start scan");
    },
  });
}
