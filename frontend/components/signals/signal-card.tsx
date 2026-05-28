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
  Quote,
  Rocket,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { SignalRead, SignalType } from "@/lib/types";
import { cn } from "@/lib/utils/cn";
import { formatRelative } from "@/lib/utils/dates";

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
  other: Quote,
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

type SignalCardProps = {
  signal: SignalRead;
  onViewEvidence?: (signal: SignalRead) => void;
};

export function SignalCard({ signal, onViewEvidence }: SignalCardProps) {
  const Icon = SIGNAL_ICON[signal.signal_type];
  const confidencePct = Math.round((signal.confidence ?? 0) * 100);
  const evidenceHost = (() => {
    try {
      return new URL(signal.evidence_url).hostname.replace(/^www\./, "");
    } catch {
      return signal.evidence_url;
    }
  })();

  return (
    <article className="flex flex-col gap-3 rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] p-4 shadow-[var(--shadow-flat)] transition-colors hover:border-[color:var(--color-border-strong)]">
      <header className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <span className="grid size-7 shrink-0 place-items-center rounded-md bg-[color:var(--color-raised)] text-[color:var(--color-fg-secondary)]">
            <Icon className="size-3.5" aria-hidden />
          </span>
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="neutral" size="sm">
                {SIGNAL_LABEL[signal.signal_type]}
              </Badge>
              <Badge
                variant={
                  confidencePct >= 70
                    ? "signal"
                    : confidencePct >= 50
                      ? "evidence"
                      : "neutral"
                }
                size="sm"
              >
                {confidencePct}% confidence
              </Badge>
              <span className="text-[11px] text-[color:var(--color-fg-muted)]">
                {formatRelative(signal.observed_at ?? signal.created_at)}
              </span>
            </div>
            <h3 className="text-[14px] font-semibold leading-snug text-[color:var(--color-fg-primary)]">
              {signal.title}
            </h3>
          </div>
        </div>
      </header>

      {signal.fact_text ? (
        <p className="text-[13px] leading-relaxed text-[color:var(--color-fg-primary)]">
          {signal.fact_text}
        </p>
      ) : null}

      {signal.inference_text ? (
        <p
          className={cn(
            "rounded-[var(--radius-chip)] border-l-2 border-[color:var(--color-evidence)] bg-[color:var(--color-evidence-soft)]/40 px-3 py-2 text-[12px] leading-relaxed text-[color:var(--color-fg-secondary)]",
          )}
        >
          <span className="font-medium text-[color:var(--color-evidence)]">Inference. </span>
          {signal.inference_text}
        </p>
      ) : null}

      {signal.recommended_action ? (
        <p className="text-[12px] text-[color:var(--color-fg-secondary)]">
          <span className="font-medium text-[color:var(--color-fg-primary)]">Next: </span>
          {signal.recommended_action}
        </p>
      ) : null}

      <footer className="flex items-center justify-between border-t border-[color:var(--color-border-default)] pt-2">
        <span className="text-[11px] text-[color:var(--color-fg-muted)]">{evidenceHost}</span>
        <div className="flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-[12px]"
            onClick={() => onViewEvidence?.(signal)}
          >
            <Quote className="size-3" aria-hidden />
            View evidence
          </Button>
        </div>
      </footer>
    </article>
  );
}
