"use client";

import { LayoutGrid } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { AccountFilterBar } from "@/components/accounts/account-filter-bar";
import { AccountKpiStrip } from "@/components/accounts/account-kpi-strip";
import { AccountTable } from "@/components/accounts/account-table";
import { TopCommandBar } from "@/components/app-shell/top-command-bar";
import { EmptyState } from "@/components/primitives/empty-state";
import { Button } from "@/components/ui/button";
import { COPY } from "@/lib/copy";
import { useAccountsList } from "@/lib/hooks/use-accounts";
import { useAutoPrimeSeed } from "@/lib/hooks/use-auto-prime-seed";
import type { AccountListFilters, AccountStatus } from "@/lib/types";

export function AccountsPageClient() {
  const params = useSearchParams();
  const filters: AccountListFilters = {
    search: params.get("search") ?? undefined,
    status: (params.get("status") as AccountStatus | null) ?? undefined,
    sales_ready: params.get("sales_ready") === "true" ? true : undefined,
    near_miss: params.get("near_miss") === "true" ? true : undefined,
    limit: 100,
    offset: 0,
  };

  const accountsQuery = useAccountsList(filters);
  // Probe the unfiltered list so we know if the workspace is genuinely empty
  // (which triggers auto-prime), independent of any active filters.
  const baseQuery = useAccountsList({ limit: 1 });
  const isWorkspaceEmpty = baseQuery.isSuccess && (baseQuery.data?.total ?? 0) === 0;
  const { isPriming } = useAutoPrimeSeed({
    isReady: baseQuery.isSuccess,
    isEmpty: isWorkspaceEmpty,
  });

  const rows = accountsQuery.data?.items ?? [];
  const total = accountsQuery.data?.total ?? 0;
  const hasFilters = Boolean(
    filters.search || filters.status || filters.sales_ready || filters.near_miss,
  );

  return (
    <>
      <TopCommandBar
        title="Accounts"
        subtitle="Live GTM change intelligence"
        primaryAction={
          <Button asChild size="sm" variant="primary">
            <Link href="/imports">Import seed</Link>
          </Button>
        }
      />
      <div className="flex flex-col gap-5 px-6 py-5">
        <AccountKpiStrip />
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between gap-3">
            <AccountFilterBar />
            <span className="text-[12px] tabular-nums text-[color:var(--color-fg-muted)]">
              {accountsQuery.isFetching ? "loading…" : `${total} ${total === 1 ? "account" : "accounts"}`}
            </span>
          </div>

          {accountsQuery.isError ? (
            <EmptyState
              icon={LayoutGrid}
              title="Could not load accounts"
              body="Make sure the Tendril backend is running on port 8000."
            />
          ) : rows.length === 0 && !accountsQuery.isLoading ? (
            isPriming ? (
              <EmptyState
                icon={LayoutGrid}
                title="Loading demo seed"
                body="Priming the workspace with five seeded accounts and prior champions."
              />
            ) : hasFilters ? (
              <EmptyState
                icon={LayoutGrid}
                title="No matches"
                body="Try clearing filters or adjusting your search."
              />
            ) : (
              <EmptyState
                icon={LayoutGrid}
                title={COPY.empty.accountsTitle}
                body={COPY.empty.accountsBody}
                action={
                  <Button asChild size="sm">
                    <Link href="/imports">Import seed CSV</Link>
                  </Button>
                }
              />
            )
          ) : (
            <AccountTable rows={rows} isLoading={accountsQuery.isLoading} />
          )}
        </div>
      </div>
    </>
  );
}
