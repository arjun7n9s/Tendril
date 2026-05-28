"use client";

import { useState } from "react";

import { TopCommandBar } from "@/components/app-shell/top-command-bar";
import { EmptyOutreachIllustration } from "@/components/illustrations";
import { DraftEditor } from "@/components/outreach/draft-editor";
import { DraftQueue } from "@/components/outreach/draft-queue";
import { GuardrailPanel } from "@/components/outreach/guardrail-panel";
import { EmptyState } from "@/components/primitives/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { COPY } from "@/lib/copy";
import { useOutreachDraft, usePendingOutreach } from "@/lib/hooks/use-outreach";

export function OutreachCockpitClient() {
  const queueQuery = usePendingOutreach();
  const drafts = queueQuery.data?.items ?? [];

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const activeId = selectedId ?? drafts[0]?.id ?? null;

  const draftQuery = useOutreachDraft(activeId);

  return (
    <>
      <TopCommandBar
        title="Outreach review"
        subtitle="Human approval before any draft leaves Tendril"
      />
      <div className="grid h-[calc(100vh-64px)] grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)_320px]">
        <aside className="border-r border-[color:var(--color-border-default)] bg-[color:var(--color-surface)]">
          <DraftQueue
            drafts={drafts}
            selectedId={activeId}
            onSelect={setSelectedId}
            isLoading={queueQuery.isLoading}
          />
        </aside>

        <section className="flex flex-col overflow-y-auto px-6 py-5">
          {draftQuery.isLoading ? (
            <div className="flex flex-col gap-3">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-64 w-full" />
            </div>
          ) : draftQuery.data ? (
            <DraftEditor key={draftQuery.data.id} draft={draftQuery.data} />
          ) : (
            <EmptyState
              illustration={<EmptyOutreachIllustration />}
              illustrationTone="evidence"
              title="No pending drafts"
              body={COPY.outreach.queueEmpty}
            />
          )}
        </section>

        <aside className="hidden border-l border-[color:var(--color-border-default)] bg-[color:var(--color-canvas)] p-4 lg:block">
          {draftQuery.data ? (
            <GuardrailPanel draft={draftQuery.data} />
          ) : (
            <p className="text-[12px] text-[color:var(--color-fg-muted)]">
              Select a draft to inspect its guardrails.
            </p>
          )}
        </aside>
      </div>
    </>
  );
}
