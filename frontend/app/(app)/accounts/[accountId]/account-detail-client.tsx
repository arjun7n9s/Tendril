"use client";

import { Activity } from "lucide-react";
import Link from "next/link";

import { AccountHeader } from "@/components/accounts/account-header";
import { AccountScoreStrip } from "@/components/accounts/account-score-strip";
import { TopCommandBar } from "@/components/app-shell/top-command-bar";
import { AccountBriefPanel } from "@/components/briefs/account-brief-panel";
import { EmptyState } from "@/components/primitives/empty-state";
import { SectionHeading } from "@/components/primitives/section-heading";
import { SignalCard } from "@/components/signals/signal-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAccountDetail } from "@/lib/hooks/use-accounts";

type Props = { accountId: string };

export function AccountDetailClient({ accountId }: Props) {
  const detail = useAccountDetail(accountId);

  if (detail.isLoading) {
    return (
      <>
        <TopCommandBar title="Loading…" />
        <div className="flex flex-col gap-5 px-6 py-5">
          <Skeleton className="h-32 rounded-[var(--radius-card)]" />
          <Skeleton className="h-48 rounded-[var(--radius-card)]" />
        </div>
      </>
    );
  }

  if (detail.isError || !detail.data) {
    return (
      <>
        <TopCommandBar title="Account" />
        <div className="px-6 py-10">
          <EmptyState
            icon={Activity}
            title="Account not found"
            body="The requested account does not exist or the backend is unreachable."
            action={
              <Button asChild size="sm">
                <Link href="/accounts">Back to accounts</Link>
              </Button>
            }
          />
        </div>
      </>
    );
  }

  const { account, latest_scan, latest_score, latest_brief, recent_signals } = detail.data;

  return (
    <>
      <TopCommandBar
        title={account.name}
        subtitle={account.domain ?? "No domain on file"}
        primaryAction={
          <Button asChild variant="ghost" size="sm">
            <Link href="/accounts">All accounts</Link>
          </Button>
        }
      />
      <div className="flex flex-col gap-5">
        <AccountHeader account={account} lastScannedAt={latest_scan?.completed_at} />

        <div className="flex flex-col gap-5 px-6 pb-8">
          <AccountScoreStrip score={latest_score} brief={latest_brief} />

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
            <section className="flex flex-col gap-3">
              <SectionHeading
                title="Signals"
                description={
                  recent_signals.length > 0
                    ? `${recent_signals.length} from latest scan`
                    : "No signals yet"
                }
              />

              {recent_signals.length === 0 ? (
                <EmptyState
                  icon={Activity}
                  title="No signals yet"
                  body="Run a live scan to discover hiring, migration, and champion changes for this account."
                />
              ) : (
                <div className="flex flex-col gap-3">
                  {recent_signals.map((signal) => (
                    <SignalCard key={signal.id} signal={signal} />
                  ))}
                </div>
              )}
            </section>

            <aside className="flex flex-col gap-4">
              <AccountBriefPanel brief={latest_brief} />
              <PlaceholderPanel
                title="Outreach draft"
                body="Approved drafts ship to the outreach review cockpit. The Phase 2 build wires the human-in-the-loop editor here."
              />
            </aside>
          </div>
        </div>
      </div>
    </>
  );
}

function PlaceholderPanel({ title, body }: { title: string; body: string }) {
  return (
    <section className="rounded-[var(--radius-card)] border border-dashed border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] p-4">
      <h3 className="text-[13px] font-semibold tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
        {title}
      </h3>
      <p className="mt-1 text-[13px] text-[color:var(--color-fg-muted)]">{body}</p>
    </section>
  );
}
