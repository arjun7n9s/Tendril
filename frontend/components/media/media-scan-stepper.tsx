"use client";

import { Check, CircleDashed, Loader2, OctagonX } from "lucide-react";

import { type MediaScanStage, MEDIA_SCAN_STAGES_ORDERED } from "@/lib/types";
import { cn } from "@/lib/utils/cn";

const STAGE_LABEL: Record<MediaScanStage, string> = {
  queued: "Queued",
  discover_sources: "Discovering conversations",
  rank_sources: "Ranking sources",
  resolve_media: "Resolving media",
  hash_media: "Checking transcript cache",
  transcribe: "Transcribing",
  scrub_transcript: "Scrubbing transcript",
  extract_signals: "Extracting signals",
  write_memory: "Updating memory",
  score_account: "Refreshing score",
  notify: "Notifying",
  completed: "Ready",
  failed: "Failed",
};

type StepState = "pending" | "active" | "complete" | "failed";

function stateForStage(current: MediaScanStage, stage: MediaScanStage): StepState {
  if (current === "completed") return "complete";
  if (current === "failed") {
    const stageIndex = MEDIA_SCAN_STAGES_ORDERED.indexOf(stage);
    const currentIndex = MEDIA_SCAN_STAGES_ORDERED.indexOf(stage);
    // We don't know exactly which stage failed from status alone, so mark
    // the active pointer as failed and everything before it complete.
    return stageIndex < currentIndex ? "complete" : "failed";
  }
  const currentIndex = MEDIA_SCAN_STAGES_ORDERED.indexOf(current);
  const stageIndex = MEDIA_SCAN_STAGES_ORDERED.indexOf(stage);
  if (currentIndex === -1) return "pending";
  if (stageIndex < currentIndex) return "complete";
  if (stageIndex === currentIndex) return "active";
  return "pending";
}

export function MediaScanStepper({
  status,
  currentStage,
}: {
  status: MediaScanStage;
  currentStage: MediaScanStage;
}) {
  // When the job failed, use current_stage to locate the failure point.
  const pointer = status === "failed" ? currentStage : status;

  return (
    <ol className="flex flex-col gap-1">
      {MEDIA_SCAN_STAGES_ORDERED.map((stage) => {
        let state = stateForStage(pointer, stage);
        if (status === "failed") {
          const idx = MEDIA_SCAN_STAGES_ORDERED.indexOf(stage);
          const failIdx = MEDIA_SCAN_STAGES_ORDERED.indexOf(currentStage);
          state = idx < failIdx ? "complete" : idx === failIdx ? "failed" : "pending";
        }
        return (
          <li key={stage} className="flex items-center gap-2">
            <span
              className={cn(
                "grid size-4 shrink-0 place-items-center rounded-full",
                state === "active" && "text-[color:var(--color-cobalt)]",
                state === "complete" && "text-[color:var(--color-signal)]",
                state === "failed" && "text-[color:var(--color-risk)]",
                state === "pending" && "text-[color:var(--color-fg-muted)]",
              )}
            >
              {state === "active" ? (
                <Loader2 className="size-3.5 animate-spin" aria-hidden />
              ) : state === "complete" ? (
                <Check className="size-3.5" aria-hidden />
              ) : state === "failed" ? (
                <OctagonX className="size-3.5" aria-hidden />
              ) : (
                <CircleDashed className="size-3.5" aria-hidden />
              )}
            </span>
            <span
              className={cn(
                "text-[12px]",
                state === "active" && "font-semibold text-fg-primary",
                state === "complete" && "text-fg-secondary",
                state === "failed" && "font-semibold text-[color:var(--color-risk)]",
                state === "pending" && "text-fg-muted",
              )}
            >
              {STAGE_LABEL[stage]}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
