"use client";

import { ArrowUpRight } from "lucide-react";
import Link from "next/link";

import { StatusChip } from "@/components/primitives/status-chip";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { COPY } from "@/lib/copy";
import { usePendingOutreach } from "@/lib/hooks/use-outreach";

export function AccountOutreachPreview({ accountId }: { accountId: string }) {
  const queueQuery = usePendingOutreach();
  const draft = (queueQuery.data?.items ?? []).find((d) => d.account_id === accountId) ?? null;

  if (queueQuery.isLoading) {
    return <Skeleton className="h-32 rounded-[var(--radius-card)]" />;
  }

  if (!draft) {
    return (
      <section className="rounded-[var(--radius-card)] border border-dashed border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] p-4">
        <h3 className="text-[13px] font-semibold tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
          Outreach draft
        </h3>
        <p className="mt-1 text-[13px] text-[color:var(--color-fg-muted)]">
          Sales-ready scans automatically generate a draft for review. Run a scan to populate this
          panel.
        </p>
      </section>
    );
  }

  return (
    <section className="flex flex-col gap-3 rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] p-4 shadow-[var(--shadow-flat)]">
      <header className="flex items-center justify-between gap-2">
        <h3 className="text-[13px] font-semibold tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
          Outreach draft
        </h3>
        <StatusChip kind="outreach" value={draft.status} size="sm" />
      </header>
      <div className="flex flex-col gap-1">
        <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-muted)]">
          Subject
        </span>
        <p className="text-[13px] font-medium text-[color:var(--color-fg-primary)]">
          {draft.subject}
        </p>
      </div>
      <p className="line-clamp-4 text-[12px] leading-relaxed text-[color:var(--color-fg-secondary)]">
        {draft.body}
      </p>
      <p className="text-[11px] text-[color:var(--color-fg-muted)]">
        {COPY.outreach.guardrailHeading.toLowerCase()} · tone {draft.tone}
      </p>
      <Button asChild variant="secondary" size="sm" className="self-start">
        <Link href="/outreach">
          <span>Open in cockpit</span>
          <ArrowUpRight className="size-3" aria-hidden />
        </Link>
      </Button>
    </section>
  );
}
