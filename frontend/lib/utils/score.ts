import type { ScoreRead } from "@/lib/types";

export type ScoreTier = "sales-ready" | "near-miss" | "watch" | "low";

/**
 * Tendril uses a tiered visual treatment instead of a continuous gradient
 * because the backend already publishes discrete score thresholds in
 * backend_implementation_plan.md and backend_requirements_checklist.md:
 *
 *   - sales-ready: total >= 70 (and the backend already marks the boolean)
 *   - near-miss : 55-69 with sales_ready=false
 *   - watch     : 40-54
 *   - low       : 0-39
 */
export function scoreTier(score: Pick<ScoreRead, "total_score" | "sales_ready"> | null | undefined): ScoreTier {
  if (!score) return "low";
  if (score.sales_ready) return "sales-ready";
  if (score.total_score >= 55) return "near-miss";
  if (score.total_score >= 40) return "watch";
  return "low";
}

export function scoreTierLabel(tier: ScoreTier): string {
  switch (tier) {
    case "sales-ready":
      return "Sales-ready";
    case "near-miss":
      return "Needs one more signal";
    case "watch":
      return "Watch";
    case "low":
      return "Low priority";
  }
}

export function scoreTierAccent(tier: ScoreTier): {
  fg: string;
  bg: string;
  border: string;
  ring: string;
} {
  switch (tier) {
    case "sales-ready":
      return {
        fg: "text-[color:var(--color-signal)]",
        bg: "bg-[color:var(--color-signal-soft)]",
        border: "border-[color:color-mix(in_oklab,var(--color-signal)_30%,transparent)]",
        ring: "stroke-[color:var(--color-signal)]",
      };
    case "near-miss":
      return {
        fg: "text-[color:var(--color-evidence)]",
        bg: "bg-[color:var(--color-evidence-soft)]",
        border: "border-[color:color-mix(in_oklab,var(--color-evidence)_30%,transparent)]",
        ring: "stroke-[color:var(--color-evidence)]",
      };
    case "watch":
      return {
        fg: "text-[color:var(--color-cobalt)]",
        bg: "bg-[color:var(--color-cobalt-soft)]",
        border: "border-[color:color-mix(in_oklab,var(--color-cobalt)_25%,transparent)]",
        ring: "stroke-[color:var(--color-cobalt)]",
      };
    case "low":
      return {
        fg: "text-[color:var(--color-fg-secondary)]",
        bg: "bg-[color:var(--color-raised)]",
        border: "border-[color:var(--color-border-default)]",
        ring: "stroke-[color:var(--color-border-strong)]",
      };
  }
}
