"use client";

import { useQueries } from "@tanstack/react-query";
import { useMemo } from "react";

import { accountsApi } from "@/lib/api";
import type { AccountRead, ScanRead } from "@/lib/types";

export type AccountScanRow = {
  account: AccountRead;
  latest_scan: ScanRead | null;
};

/**
 * Cross-account scans list, derived from per-account detail fetches.
 *
 * The backend does not expose a `/scans` collection endpoint yet, so
 * for the hackathon demo we fan out small parallel queries (one per
 * account) using TanStack's `useQueries`. Each query reuses the
 * cached account detail when present, which keeps the UI snappy after
 * users have already opened a few account pages.
 */
export function useCrossAccountScans(accounts: AccountRead[]) {
  const results = useQueries({
    queries: accounts.map((account) => ({
      queryKey: ["account", account.id],
      queryFn: ({ signal }: { signal?: AbortSignal }) =>
        accountsApi.getAccount(account.id, signal),
      // Detail endpoints are cheap and we want fresh scan status.
      staleTime: 15_000,
    })),
  });

  return useMemo(() => {
    return accounts.map<AccountScanRow>((account, idx) => {
      const data = results[idx]?.data;
      return {
        account,
        latest_scan: data?.latest_scan ?? null,
      };
    });
  }, [accounts, results]);
}
