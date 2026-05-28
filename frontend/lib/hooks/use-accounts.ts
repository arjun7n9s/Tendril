"use client";

import { useQuery } from "@tanstack/react-query";

import { accountsApi } from "@/lib/api";
import type { AccountListFilters } from "@/lib/types";

export function useAccountsList(filters: AccountListFilters = {}) {
  return useQuery({
    queryKey: ["accounts", filters],
    queryFn: ({ signal }) => accountsApi.listAccounts(filters, signal),
  });
}

export function useAccountDetail(accountId: string | undefined) {
  return useQuery({
    queryKey: ["account", accountId],
    queryFn: ({ signal }) => accountsApi.getAccount(accountId!, signal),
    enabled: Boolean(accountId),
  });
}
