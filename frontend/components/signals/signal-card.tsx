"use client";

import {
  ArrowRightLeft,
  Banknote,
  Briefcase,
  Compass,
  Cpu,
  Crosshair,
  ExternalLink,
  Flame,
  type LucideIcon,
  Quote,
  Rocket,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useEvidenceDrawer } from "@/components/evidence/evidence-drawer-context";
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
};

export function SignalCard({ signal }: SignalCardProps) {
  const drawer = useEvidenceDrawer();
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
    <article className="flex flex-col gap-3 rounded-[var(--radius-card)] border border-border/40 bg-surface/85 p-4 shadow-flat transition-all duration-300 ease-out hover:border-border/80 hover:shadow-raised hover:scale-[1.003] hover:-translate-y-[0.5px]">
      <header className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <span className="grid size-7 shrink-0 place-items-center rounded-md bg-raised border border-border/40 text-fg-secondary">
            <Icon className="size-3.5" aria-hidden />
          </span>
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="neutral" size="sm" className="font-semibold tracking-[0.01em]">
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
                className="inline-flex items-center gap-1 font-semibold transition-colors duration-300"
              >
                {confidencePct >= 70 && (
                  <span className="relative flex h-1.5 w-1.5 shrink-0" aria-hidden>
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-signal opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-signal"></span>
                  </span>
                )}
                {confidencePct}% confidence
              </Badge>
              <span className="text-[11px] text-fg-muted font-medium">
                {formatRelative(signal.observed_at ?? signal.created_at)}
              </span>
            </div>
            <h3 className="text-[14px] font-semibold leading-snug text-fg-primary tracking-[-0.01em]">
              {signal.title}
            </h3>
          </div>
        </div>
      </header>

      {signal.fact_text ? (
        <p className="text-[13px] leading-relaxed text-fg-primary">
          {signal.fact_text}
        </p>
      ) : null}

      {signal.inference_text ? (
        <p
          className={cn(
            "rounded-r-[var(--radius-chip)] border-l-2 border-evidence bg-evidence-soft/30 px-3 py-2 text-[12px] leading-relaxed text-fg-secondary backdrop-blur-sm",
          )}
        >
          <span className="font-semibold text-evidence">Inference · </span>
          {signal.inference_text}
        </p>
      ) : null}

      {signal.recommended_action ? (
        <div className="flex items-start gap-2 rounded-[var(--radius-chip)] border border-border/40 bg-raised/35 px-3 py-2 text-[12px] leading-normal text-fg-secondary">
          <span className="font-semibold text-fg-primary select-none">Next Steps:</span>
          <span>{signal.recommended_action}</span>
        </div>
      ) : null}

      <footer className="flex items-center justify-between border-t border-border/30 pt-2.5 mt-0.5">
        <a
          href={signal.evidence_url}
          target="_blank"
          rel="noreferrer"
          className="group/source inline-flex items-center gap-1 text-[11px] text-fg-muted transition-colors hover:text-fg-primary focus-visible:text-fg-primary"
          aria-label={`Open original source ${evidenceHost} in a new tab`}
        >
          {evidenceHost}
          <ExternalLink
            className="size-3 opacity-0 -translate-x-0.5 translate-y-0.5 transition-all duration-200 group-hover/source:opacity-100 group-hover/source:translate-x-0 group-hover/source:translate-y-0"
            aria-hidden
          />
        </a>
        <div className="flex items-center gap-1.5">
          <Button
            variant="secondary"
            size="sm"
            className="h-7 px-2 text-[11.5px] font-semibold border border-border/60 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
            onClick={() => drawer.open({ kind: "signal", signal })}
          >
            <Quote className="size-3 text-cobalt" aria-hidden />
            View evidence
          </Button>
        </div>
      </footer>
    </article>
  );
}
