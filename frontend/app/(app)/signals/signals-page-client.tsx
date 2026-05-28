"use client";

import { Sparkles, X } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";

import { TopCommandBar } from "@/components/app-shell/top-command-bar";
import { EvidenceDrawerProvider } from "@/components/evidence/evidence-drawer-context";
import {
  EmptySignalsIllustration,
  ErrorStateIllustration,
} from "@/components/illustrations";
import { EmptyState } from "@/components/primitives/empty-state";
import { MonogramTile } from "@/components/primitives/monogram-tile";
import { SignalCard } from "@/components/signals/signal-card";
import { SignalTypeFilter } from "@/components/signals/signal-type-filter";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAccountsList } from "@/lib/hooks/use-accounts";
import { useSignalsList } from "@/lib/hooks/use-signals";
import type { SignalRead, SignalType } from "@/lib/types";

export function SignalsPageClient() {
  const router = useRouter();
  const params = useSearchParams();

  const signalType = (params.get("type") as SignalType | null) ?? null;
  const minConfidence = params.get("min_conf") ? Number(params.get("min_conf")) : null;
  const salesReady = params.get("sales_ready") === "true";

  const setParam = useCallback(
    (key: string, value: string | null) => {
      const next = new URLSearchParams(params.toString());
      if (value === null || value === "") next.delete(key);
      else next.set(key, value);
      const qs = next.toString();
      router.replace(qs ? `?${qs}` : "?");
    },
    [params, router],
  );

  const signalsQuery = useSignalsList({
    signal_type: signalType ?? undefined,
    min_confidence: minConfidence ?? undefined,
    sales_ready: salesReady ? true : undefined,
    limit: 200,
  });
  const accountsQuery = useAccountsList({ limit: 200 });

  const accountsById = useMemo(() => {
    const map = new Map<string, { name: string; domain?: string | null }>();
    for (const account of accountsQuery.data?.items ?? []) {
      map.set(account.id, { name: account.name, domain: account.domain });
    }
    return map;
  }, [accountsQuery.data]);

  const grouped = useMemo(() => {
    const byAccount = new Map<string, SignalRead[]>();
    for (const signal of signalsQuery.data?.items ?? []) {
      const list = byAccount.get(signal.account_id) ?? [];
      list.push(signal);
      byAccount.set(signal.account_id, list);
    }
    return Array.from(byAccount.entries()).sort((a, b) => b[1].length - a[1].length);
  }, [signalsQuery.data]);

  const total = signalsQuery.data?.total ?? 0;
  const filtersApplied = Boolean(signalType || minConfidence || salesReady);

  return (
    <EvidenceDrawerProvider>
      <TopCommandBar
        title="Signal feed"
        subtitle="Cross-account intelligence from the latest scans"
      />
      <div className="flex flex-col gap-5 px-6 py-5">
        <div className="flex flex-col gap-3 rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] p-3">
          <div className="flex flex-wrap items-center gap-3">
            <SignalTypeFilter
              value={signalType}
              onChange={(next) => setParam("type", next)}
            />
            <button
              type="button"
              onClick={() => setParam("sales_ready", salesReady ? null : "true")}
              className={`inline-flex h-7 items-center gap-1.5 rounded-[var(--radius-button)] border px-2 text-[12px] transition-colors ${
                salesReady
                  ? "border-[color:color-mix(in_oklab,var(--color-signal)_30%,transparent)] bg-[color:var(--color-signal-soft)] text-[color:var(--color-signal)]"
                  : "border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] text-[color:var(--color-fg-secondary)] hover:bg-[color:var(--color-raised)]"
              }`}
            >
              <Sparkles className="size-3" aria-hidden />
              Sales-ready scans only
            </button>
            <ConfidenceFilter
              value={minConfidence}
              onChange={(next) => setParam("min_conf", next === null ? null : String(next))}
            />
            {filtersApplied ? (
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-[12px] text-[color:var(--color-fg-secondary)]"
                onClick={() => router.replace("?")}
              >
                <X className="size-3" aria-hidden />
                Clear
              </Button>
            ) : null}
            <span className="ml-auto text-[12px] tabular-nums text-[color:var(--color-fg-muted)]">
              {signalsQuery.isFetching
                ? "loading…"
                : `${total} ${total === 1 ? "signal" : "signals"}`}
            </span>
          </div>
        </div>

        {signalsQuery.isError ? (
          <EmptyState
            illustration={<ErrorStateIllustration />}
            illustrationTone="risk"
            title="Could not load signals"
            body="Make sure the Tendril backend is running on port 8000."
          />
        ) : signalsQuery.isLoading ? (
          <div className="flex flex-col gap-3">
            {Array.from({ length: 4 }).map((_, idx) => (
              <Skeleton key={idx} className="h-32 rounded-[var(--radius-card)]" />
            ))}
          </div>
        ) : grouped.length === 0 ? (
          <EmptyState
            illustration={<EmptySignalsIllustration />}
            illustrationTone="cobalt"
            title="No signals match"
            body={
              filtersApplied
                ? "Try clearing filters or running a fresh scan."
                : "Run a scan from any account to populate the feed."
            }
          />
        ) : (
          <div className="flex flex-col gap-6">
            {grouped.map(([accountId, accountSignals]) => {
              const account = accountsById.get(accountId);
              return (
                <section key={accountId} className="flex flex-col gap-3">
                  <header className="flex items-center justify-between gap-2">
                    <Link
                      href={`/accounts/${accountId}`}
                      className="inline-flex items-center gap-2 text-[14px] font-semibold text-[color:var(--color-fg-primary)] hover:underline"
                    >
                      <MonogramTile
                        name={account?.name ?? accountId}
                        seed={accountId}
                        size="sm"
                      />
                      {account?.name ?? accountId}
                      {account?.domain ? (
                        <span className="text-[12px] font-normal text-[color:var(--color-fg-muted)]">
                          {account.domain}
                        </span>
                      ) : null}
                    </Link>
                    <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-muted)]">
                      {accountSignals.length} signal{accountSignals.length === 1 ? "" : "s"}
                    </span>
                  </header>
                  <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
                    {accountSignals.map((signal) => (
                      <SignalCard key={signal.id} signal={signal} />
                    ))}
                  </div>
                </section>
              );
            })}
          </div>
        )}
      </div>
    </EvidenceDrawerProvider>
  );
}

function ConfidenceFilter({
  value,
  onChange,
}: {
  value: number | null;
  onChange: (value: number | null) => void;
}) {
  const options: { label: string; value: number | null }[] = [
    { label: "Any", value: null },
    { label: "≥ 0.5", value: 0.5 },
    { label: "≥ 0.7", value: 0.7 },
    { label: "≥ 0.85", value: 0.85 },
  ];
  return (
    <div className="inline-flex items-center gap-0.5 rounded-[var(--radius-button)] border border-[color:var(--color-border-default)] bg-[color:var(--color-raised)] p-0.5">
      {options.map((option) => {
        const active = value === option.value || (value === null && option.value === null);
        return (
          <button
            key={String(option.value)}
            type="button"
            onClick={() => onChange(option.value)}
            className={`h-6 rounded-[calc(var(--radius-button)-2px)] px-2 text-[11px] font-medium transition-colors ${
              active
                ? "bg-[color:var(--color-surface)] text-[color:var(--color-fg-primary)] shadow-[var(--shadow-flat)]"
                : "text-[color:var(--color-fg-secondary)] hover:text-[color:var(--color-fg-primary)]"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
