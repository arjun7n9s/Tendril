import { api } from "./client";
import type { AccountWatchRead, WatchUpsertRequest } from "@/lib/types";

export function getWatch(accountId: string, signal?: AbortSignal) {
  return api.get<AccountWatchRead | null>(`/api/v1/accounts/${accountId}/watch`, { signal });
}

export function upsertWatch(
  accountId: string,
  body: WatchUpsertRequest,
  signal?: AbortSignal,
) {
  return api.put<AccountWatchRead>(`/api/v1/accounts/${accountId}/watch`, {
    body,
    signal,
  });
}

export function deleteWatch(accountId: string, signal?: AbortSignal) {
  return api.delete<void>(`/api/v1/accounts/${accountId}/watch`, { signal });
}
