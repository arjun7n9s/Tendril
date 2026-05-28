"use client";

import { Check, CircleDashed, Loader2, OctagonX } from "lucide-react";

import { type ScanStatus, SCAN_PHASES_ORDERED } from "@/lib/types";
import { cn } from "@/lib/utils/cn";

const PHASE_LABEL: Record<ScanStatus, string> = {
  queued: "Queued",
  discovering: "Discovering",
  scraping: "Scraping",
  extracting: "Extracting",
  graphing: "Graphing",
  scoring: "Scoring",
  briefing: "Briefing",
  completed: "Ready",
  failed: "Failed",
};

type StepState = "pending" | "active" | "complete" | "failed";

function stateForPhase(current: ScanStatus, phase: ScanStatus): StepState {
  if (current === "failed") {
    const currentIndex = SCAN_PHASES_ORDERED.indexOf(phase);
    const failedAt = SCAN_PHASES_ORDERED.length - 1; // unknown which phase actually failed
    if (currentIndex <= failedAt) return "complete";
    return "failed";
  }
  const currentIndex = SCAN_PHASES_ORDERED.indexOf(current);
  const phaseIndex = SCAN_PHASES_ORDERED.indexOf(phase);
  if (phaseIndex < currentIndex) return "complete";
  if (phaseIndex === currentIndex) return current === "completed" ? "complete" : "active";
  return "pending";
}

export function ScanPhaseStepper({ status }: { status: ScanStatus }) {
  return (
    <ol className="flex flex-wrap items-center gap-1.5">
      {SCAN_PHASES_ORDERED.map((phase, idx) => {
        const state = stateForPhase(status, phase);
        const isLast = idx === SCAN_PHASES_ORDERED.length - 1;
        return (
          <li key={phase} className="flex items-center gap-1.5">
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-[var(--radius-chip)] border px-1.5 py-0.5 text-[11px] font-medium transition-colors",
                state === "active" &&
                  "border-[color:color-mix(in_oklab,var(--color-cobalt)_30%,transparent)] bg-[color:var(--color-cobalt-soft)] text-[color:var(--color-cobalt)]",
                state === "complete" &&
                  "border-[color:color-mix(in_oklab,var(--color-signal)_30%,transparent)] bg-[color:var(--color-signal-soft)] text-[color:var(--color-signal)]",
                state === "pending" &&
                  "border-[color:var(--color-border-default)] bg-[color:var(--color-raised)] text-[color:var(--color-fg-muted)]",
                state === "failed" &&
                  "border-[color:color-mix(in_oklab,var(--color-risk)_30%,transparent)] bg-[color:var(--color-risk-soft)] text-[color:var(--color-risk)]",
              )}
            >
              {state === "active" ? (
                <Loader2 className="size-3 animate-spin" aria-hidden />
              ) : state === "complete" ? (
                <Check className="size-3" aria-hidden />
              ) : state === "failed" ? (
                <OctagonX className="size-3" aria-hidden />
              ) : (
                <CircleDashed className="size-3" aria-hidden />
              )}
              {PHASE_LABEL[phase]}
            </span>
            {!isLast ? (
              <span
                className={cn(
                  "h-px w-4",
                  state === "complete"
                    ? "bg-[color:var(--color-signal)]"
                    : "bg-[color:var(--color-border-default)]",
                )}
                aria-hidden
              />
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}
