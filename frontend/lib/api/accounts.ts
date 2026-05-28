import { api } from "./client";
import type {
  AccountDetailResponse,
  AccountListFilters,
  AccountListResponse,
} from "@/lib/types";

export function listAccounts(filters: AccountListFilters = {}, signal?: AbortSignal) {
  return api.get<AccountListResponse>("/api/v1/accounts", {
    params: {
      status: filters.status,
      search: filters.search,
      sales_ready: filters.sales_ready,
      near_miss: filters.near_miss,
      limit: filters.limit,
      offset: filters.offset,
    },
    signal,
  });
}

export function getAccount(accountId: string, signal?: AbortSignal) {
  return api.get<AccountDetailResponse>(`/api/v1/accounts/${accountId}`, { signal });
}
