import { api } from "./client";
import type { SignalList, SignalType } from "@/lib/types";

export type SignalListFilters = {
  account_id?: string;
  scan_id?: string;
  signal_type?: SignalType;
  min_confidence?: number;
  sales_ready?: boolean;
  limit?: number;
  offset?: number;
};

export function listSignals(filters: SignalListFilters = {}, signal?: AbortSignal) {
  return api.get<SignalList>("/api/v1/signals", { params: filters, signal });
}

export function listAccountSignals(
  accountId: string,
  filters: Omit<SignalListFilters, "account_id"> & { all_history?: boolean } = {},
  signal?: AbortSignal,
) {
  return api.get<SignalList>(`/api/v1/accounts/${accountId}/signals`, {
    params: filters,
    signal,
  });
}
