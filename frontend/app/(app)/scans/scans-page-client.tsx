"use client";

import { Radar } from "lucide-react";
import Link from "next/link";

import { TopCommandBar } from "@/components/app-shell/top-command-bar";
import { MonogramTile } from "@/components/primitives/monogram-tile";
import { StatusChip } from "@/components/primitives/status-chip";
import { EmptyState } from "@/components/primitives/empty-state";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAccountsList } from "@/lib/hooks/use-accounts";
import { useCrossAccountScans } from "@/lib/hooks/use-cross-account-scans";
import { formatRelative } from "@/lib/utils/dates";
import { cn } from "@/lib/utils/cn";
import {
  NON_TERMINAL_SCAN_STATUSES,
  TERMINAL_SCAN_STATUSES,
} from "@/lib/types";

export function ScansPageClient() {
  const accountsQuery = useAccountsList({ limit: 200 });
  const accounts = accountsQuery.data?.items ?? [];
  const rows = useCrossAccountScans(accounts);

  const active = rows.filter(
    (r) => r.latest_scan && NON_TERMINAL_SCAN_STATUSES.has(r.latest_scan.status),
  );
  const recent = rows
    .filter((r) => r.latest_scan && TERMINAL_SCAN_STATUSES.has(r.latest_scan.status))
    .sort((a, b) => {
      const aT = a.latest_scan?.completed_at ?? a.latest_scan?.created_at ?? "";
      const bT = b.latest_scan?.completed_at ?? b.latest_scan?.created_at ?? "";
      return bT.localeCompare(aT);
    });
  const never = rows.filter((r) => !r.latest_scan);

  if (accountsQuery.isLoading) {
    return (
      <>
        <TopCommandBar title="Live scans" subtitle="All scans across the workspace" />
        <div className="flex flex-col gap-3 px-6 py-5">
          {Array.from({ length: 4 }).map((_, idx) => (
            <Skeleton key={idx} className="h-16 rounded-[var(--radius-card)]" />
          ))}
        </div>
      </>
    );
  }

  return (
    <>
      <TopCommandBar title="Live scans" subtitle="All scans across the workspace" />
      <div className="flex flex-col gap-6 px-6 py-5">
        <Section
          title="Active"
          empty="No scans currently running."
          rows={active}
        />
        <Section
          title="Recent"
          empty="No completed scans yet."
          rows={recent.slice(0, 24)}
        />
        <Section
          title="Never scanned"
          empty="Every account has been scanned at least once."
          rows={never}
          dimWhenIdle
        />
        {accounts.length === 0 ? (
          <EmptyState
            icon={Radar}
            title="No accounts yet"
            body="Import a seed CSV before running scans."
            action={
              <Button asChild size="sm">
                <Link href="/imports">Import seed</Link>
              </Button>
            }
          />
        ) : null}
      </div>
    </>
  );
}

function Section({
  title,
  empty,
  rows,
  dimWhenIdle = false,
}: {
  title: string;
  empty: string;
  rows: ReturnType<typeof useCrossAccountScans>;
  dimWhenIdle?: boolean;
}) {
  return (
    <section className="flex flex-col gap-3">
      <header className="flex items-baseline justify-between gap-2 border-b border-[color:var(--color-border-default)] pb-2">
        <h2 className="text-[12px] font-semibold tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
          {title}
        </h2>
        <span className="text-[11px] tabular-nums text-[color:var(--color-fg-muted)]">
          {rows.length}
        </span>
      </header>
      {rows.length === 0 ? (
        <p className="text-[12px] text-[color:var(--color-fg-muted)]">{empty}</p>
      ) : (
        <ul className="flex flex-col">
          {rows.map(({ account, latest_scan }) => (
            <li
              key={account.id}
              className="border-b border-[color:var(--color-border-default)] last:border-b-0"
            >
              <Link
                href={`/accounts/${account.id}`}
                className={cn(
                  "flex items-center justify-between gap-3 px-2 py-2 transition-colors hover:bg-[color:var(--color-canvas)]",
                  dimWhenIdle && "opacity-90",
                )}
              >
                <div className="flex items-center gap-3">
                  <MonogramTile name={account.name} seed={account.id} size="md" />
                  <div className="flex flex-col">
                    <span className="text-[13px] font-medium text-[color:var(--color-fg-primary)]">
                      {account.name}
                    </span>
                    <span className="text-[11px] text-[color:var(--color-fg-muted)]">
                      {account.domain ?? account.industry ?? "—"}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-3 text-right">
                  {latest_scan ? (
                    <>
                      <span className="hidden text-[11px] text-[color:var(--color-fg-muted)] md:inline">
                        {formatRelative(
                          latest_scan.completed_at ?? latest_scan.created_at,
                        )}
                      </span>
                      <StatusChip kind="scan" value={latest_scan.status} />
                      <span className="hidden text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-muted)] sm:inline">
                        {latest_scan.mode}
                      </span>
                    </>
                  ) : (
                    <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-muted)]">
                      No scan
                    </span>
                  )}
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
