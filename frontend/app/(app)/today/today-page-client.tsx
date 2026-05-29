"use client";

import { ArrowRight, Mic, Sparkles, Sunrise } from "lucide-react";
import Link from "next/link";

import { TopCommandBar } from "@/components/app-shell/top-command-bar";
import { MonogramTile } from "@/components/primitives/monogram-tile";
import { MotionFade } from "@/components/primitives/motion-fade";
import { EmptyState } from "@/components/primitives/empty-state";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useTodayFeed } from "@/lib/hooks/use-today";
import type { TodayFeedItem } from "@/lib/types";
import { scoreTier, scoreTierAccent } from "@/lib/utils/score";

export function TodayPageClient() {
  const { data, isLoading, isError } = useTodayFeed(12);
  const items = data?.items ?? [];

  return (
    <>
      <TopCommandBar
        title="Today"
        subtitle="The accounts that became actionable — ranked, explained, ready to act on"
      />
      <div className="flex flex-col gap-5 px-6 py-5">
        {isLoading ? (
          <div className="flex flex-col gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-[92px] rounded-[var(--radius-card)]" />
            ))}
          </div>
        ) : isError ? (
          <EmptyState
            icon={Sunrise}
            title="Could not load Today"
            body="Make sure the Tendril backend is running on port 8000."
          />
        ) : items.length === 0 ? (
          <EmptyState
            illustration={<Sparkles className="size-8 text-cobalt" />}
            illustrationTone="cobalt"
            title="Nothing new to act on yet"
            body="Run a scan on an account to start building your daily queue. As accounts move, the highest-priority ones surface here first."
          />
        ) : (
          <ol className="flex flex-col gap-2.5">
            {items.map((item, idx) => (
              <MotionFade key={item.account_id} delay={Math.min(idx, 6) * 0.04}>
                <TodayRow item={item} rank={idx + 1} />
              </MotionFade>
            ))}
          </ol>
        )}
      </div>
    </>
  );
}

function TodayRow({ item, rank }: { item: TodayFeedItem; rank: number }) {
  const tier = scoreTier({ total_score: item.total_score, sales_ready: item.sales_ready });
  const accent = scoreTierAccent(tier);
  const spoken = item.source === "media_scan" && (item.conversation_delta ?? 0) > 0;

  return (
    <li>
      <Link
        href={`/accounts/${item.account_id}`}
        className="group flex items-center gap-4 rounded-[var(--radius-card)] border border-border bg-surface p-4 shadow-flat transition-all duration-150 hover:border-border-strong hover:shadow-raised"
      >
        <span className="w-5 shrink-0 text-center text-[12px] font-semibold tabular-nums text-fg-muted">
          {rank}
        </span>
        <MonogramTile name={item.account_name} seed={item.account_id} size="md" />
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="truncate text-[14px] font-semibold text-fg-primary">
              {item.account_name}
            </span>
            {item.reason_tags.map((tag) => (
              <Badge
                key={tag}
                variant={
                  tag === "sales-ready"
                    ? "signal"
                    : tag === "spoken-evidence"
                      ? "graph"
                      : "neutral"
                }
                size="sm"
                className="gap-1 font-semibold"
              >
                {tag === "spoken-evidence" ? <Mic className="size-3" aria-hidden /> : null}
                {tag}
              </Badge>
            ))}
          </div>
          <p className="line-clamp-1 text-[12.5px] leading-snug text-fg-secondary">
            {item.why_now}
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-0.5">
          <span className={`text-[18px] font-semibold tabular-nums ${accent.fg}`}>
            {item.total_score}
          </span>
          {spoken ? (
            <span className="text-[10.5px] font-semibold text-graph">
              +{item.conversation_delta} spoken
            </span>
          ) : (
            <span className="text-[10px] uppercase tracking-[0.04em] text-fg-muted">/100</span>
          )}
        </div>
        <ArrowRight
          className="size-4 shrink-0 text-fg-muted opacity-0 transition-opacity group-hover:opacity-100"
          aria-hidden
        />
      </Link>
    </li>
  );
}
