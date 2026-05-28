"use client";

import { Sparkles } from "lucide-react";

import { ScoreBar } from "@/components/primitives/score-bar";
import { ScoreRing } from "@/components/primitives/score-ring";
import { Badge } from "@/components/ui/badge";
import { COPY } from "@/lib/copy";
import type { BriefRead, ScoreRead } from "@/lib/types";
import { scoreTier, scoreTierAccent, scoreTierLabel } from "@/lib/utils/score";
import { cn } from "@/lib/utils/cn";

type AccountScoreStripProps = {
  score: ScoreRead | null;
  brief: BriefRead | null;
};

export function AccountScoreStrip({ score, brief }: AccountScoreStripProps) {
  const tier = scoreTier(score);
  const accent = scoreTierAccent(tier);

  return (
    <div className="grid grid-cols-1 gap-4 rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] p-4 shadow-[var(--shadow-flat)] md:grid-cols-[180px_1fr_1fr]">
      <div className="flex items-center gap-3">
        <ScoreRing score={score} size={72} strokeWidth={7} />
        <div className="flex flex-col gap-1">
          <Badge
            variant={
              tier === "sales-ready"
                ? "signal"
                : tier === "near-miss"
                  ? "evidence"
                  : tier === "watch"
                    ? "cobalt"
                    : "neutral"
            }
            size="lg"
            className={cn("inline-flex items-center gap-1")}
          >
            {tier === "sales-ready" ? <Sparkles className="size-3" aria-hidden /> : null}
            {tier === "sales-ready"
              ? COPY.badges.salesReady
              : tier === "near-miss"
                ? COPY.badges.nearMiss
                : scoreTierLabel(tier)}
          </Badge>
          <span className={cn("text-[12px]", accent.fg)}>
            {score
              ? `Total ${score.total_score}/100`
              : "No score yet — run a scan to surface evidence."}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <ScoreBar
          label="Fit"
          value={score?.fit_score ?? 0}
          max={30}
          variant="signal"
        />
        <ScoreBar
          label="Timing"
          value={score?.timing_score ?? 0}
          max={30}
          variant="cobalt"
        />
        <ScoreBar
          label="Relationship"
          value={score?.relationship_score ?? 0}
          max={20}
          variant="graph"
        />
        <ScoreBar
          label="Evidence"
          value={score?.evidence_score ?? 0}
          max={20}
          variant="evidence"
        />
      </div>

      <div className="flex flex-col justify-center gap-1">
        <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
          {COPY.brief.whyNow}
        </span>
        <p className="text-[13px] leading-snug text-[color:var(--color-fg-primary)]">
          {brief?.why_now ?? "Run a scan to generate the why-now narrative."}
        </p>
      </div>
    </div>
  );
}
