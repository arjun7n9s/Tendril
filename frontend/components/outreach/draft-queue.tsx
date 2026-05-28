"use client";

import { Megaphone } from "lucide-react";

import { EmptyState } from "@/components/primitives/empty-state";
import { MonogramTile } from "@/components/primitives/monogram-tile";
import { StatusChip } from "@/components/primitives/status-chip";
import { Skeleton } from "@/components/ui/skeleton";
import { COPY } from "@/lib/copy";
import type { OutreachRead } from "@/lib/types";
import { cn } from "@/lib/utils/cn";
import { formatRelative } from "@/lib/utils/dates";

type DraftQueueProps = {
  drafts: OutreachRead[];
  selectedId: string | null;
  onSelect: (draftId: string) => void;
  isLoading: boolean;
};

export function DraftQueue({ drafts, selectedId, onSelect, isLoading }: DraftQueueProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col gap-1 p-2">
        {Array.from({ length: 4 }).map((_, idx) => (
          <Skeleton key={idx} className="h-14 rounded-[6px]" />
        ))}
      </div>
    );
  }

  if (drafts.length === 0) {
    return (
      <div className="p-4">
        <EmptyState icon={Megaphone} title="No pending drafts" body={COPY.outreach.queueEmpty} />
      </div>
    );
  }

  return (
    <ol className="flex flex-col">
      {drafts.map((draft) => {
        const isActive = draft.id === selectedId;
        return (
          <li key={draft.id}>
            <button
              type="button"
              onClick={() => onSelect(draft.id)}
              className={cn(
                "flex w-full flex-col gap-1.5 border-b border-[color:var(--color-border-default)] px-3 py-2.5 text-left transition-colors",
                isActive
                  ? "bg-[color:var(--color-raised)]"
                  : "hover:bg-[color:var(--color-canvas)]",
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <MonogramTile name={draft.account_id} seed={draft.account_id} size="sm" />
                  <span className="text-[12px] font-semibold text-[color:var(--color-fg-primary)]">
                    {draft.account_id.replace(/^acc_/, "").slice(0, 6)}…
                  </span>
                </div>
                <StatusChip kind="outreach" value={draft.status} size="sm" />
              </div>
              <span className="line-clamp-2 text-[12px] text-[color:var(--color-fg-secondary)]">
                {draft.subject}
              </span>
              <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-muted)]">
                {draft.tone} · {formatRelative(draft.created_at)}
              </span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}
