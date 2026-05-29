"use client";

import {
  ArrowRightLeft,
  Banknote,
  Briefcase,
  Compass,
  Cpu,
  Crosshair,
  Flame,
  type LucideIcon,
  Mic,
  Quote,
  Rocket,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ConversationSignalRead, SignalType } from "@/lib/types";
import { formatRelative } from "@/lib/utils/dates";
import { formatTimecode } from "@/lib/utils/timecode";

import { useConversationDrawer } from "./conversation-drawer-context";

const SIGNAL_ICON: Record<SignalType, LucideIcon> = {
  hiring: Briefcase,
  tech_stack: Cpu,
  migration: ArrowRightLeft,
  funding: Banknote,
  product_launch: Rocket,
  leadership_change: Users,
  competitor_mention: Crosshair,
  champion_move: Compass,
  market_event: Flame,
  other: Mic,
};

const SIGNAL_LABEL: Record<SignalType, string> = {
  hiring: "Hiring",
  tech_stack: "Tech stack",
  migration: "Migration",
  funding: "Funding",
  product_launch: "Product launch",
  leadership_change: "Leadership change",
  competitor_mention: "Competitor mention",
  champion_move: "Champion move",
  market_event: "Market event",
  other: "Signal",
};

export function ConversationSignalCard({ signal }: { signal: ConversationSignalRead }) {
  const drawer = useConversationDrawer();
  const Icon = SIGNAL_ICON[signal.signal_type];
  const confidencePct = Math.round((signal.confidence ?? 0) * 100);

  const host = (() => {
    try {
      return new URL(signal.source_url).hostname.replace(/^www\./, "");
    } catch {
      return signal.source_url;
    }
  })();

  return (
    <article className="flex flex-col gap-3 rounded-[var(--radius-card)] border border-border bg-surface p-4 shadow-flat transition-all duration-150 hover:border-border-strong hover:shadow-raised">
      <header className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <span className="grid size-7 shrink-0 place-items-center rounded-md border border-border bg-raised text-fg-secondary">
            <Icon className="size-3.5" aria-hidden />
          </span>
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="neutral" size="sm" className="font-semibold tracking-[0.01em]">
                {SIGNAL_LABEL[signal.signal_type]}
              </Badge>
              <Badge variant="graph" size="sm" className="gap-1 font-semibold">
                <Mic className="size-3" aria-hidden />
                Spoken
              </Badge>
              <Badge
                variant={
                  confidencePct >= 70 ? "signal" : confidencePct >= 50 ? "evidence" : "neutral"
                }
                size="sm"
                className="font-semibold"
              >
                {confidencePct}% confidence
              </Badge>
              <span className="text-[11px] font-medium text-fg-muted">
                {formatRelative(signal.observed_at ?? signal.created_at)}
              </span>
            </div>
            <h3 className="text-[14px] font-semibold leading-snug tracking-[-0.01em] text-fg-primary">
              {signal.title}
            </h3>
          </div>
        </div>
      </header>

      {signal.quote_text ? (
        <blockquote className="rounded-r-[var(--radius-chip)] border-l-2 border-evidence bg-raised px-3 py-2 text-[12.5px] leading-relaxed text-fg-secondary">
          <span className="text-fg-primary">“{signal.quote_text}”</span>
          <span className="mt-1 flex items-center gap-1.5 text-[10.5px] uppercase tracking-[0.04em] text-fg-muted">
            <Quote className="size-3" aria-hidden />
            {signal.speaker_label ?? "Speaker"}
            <span className="font-mono tabular-nums">
              · {formatTimecode(signal.quote_start_seconds)}
            </span>
          </span>
        </blockquote>
      ) : signal.fact_text ? (
        <p className="text-[13px] leading-relaxed text-fg-primary">{signal.fact_text}</p>
      ) : null}

      <footer className="mt-0.5 flex items-center justify-between border-t border-border-default pt-2.5">
        <span className="truncate text-[11px] text-fg-muted">{host}</span>
        <Button
          variant="secondary"
          size="sm"
          className="h-7 border border-border-default px-2.5 text-[11.5px] font-medium transition-colors duration-150 hover:bg-raised"
          onClick={() => drawer.open(signal)}
        >
          <Quote className="size-3 text-fg-secondary" aria-hidden />
          View evidence
        </Button>
      </footer>
    </article>
  );
}
