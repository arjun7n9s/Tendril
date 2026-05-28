"use client";

import { useQuery } from "@tanstack/react-query";

import { signalsApi } from "@/lib/api";
import type { SignalListFilters } from "@/lib/api/signals";

export function useSignalsList(filters: SignalListFilters = {}) {
  return useQuery({
    queryKey: ["signals", filters],
    queryFn: ({ signal }) => signalsApi.listSignals(filters, signal),
  });
}

type AccountSignalsFilters = Omit<SignalListFilters, "account_id"> & {
  all_history?: boolean;
};

export function useAccountSignals(
  accountId: string | undefined,
  filters: AccountSignalsFilters = {},
) {
  return useQuery({
    queryKey: ["account-signals", accountId, filters],
    queryFn: ({ signal }) => signalsApi.listAccountSignals(accountId!, filters, signal),
    enabled: Boolean(accountId),
  });
}
