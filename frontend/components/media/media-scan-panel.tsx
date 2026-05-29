"use client";

import { useQueryClient } from "@tanstack/react-query";
import { AudioLines, RotateCcw } from "lucide-react";
import { useEffect, useRef } from "react";
import { toast } from "sonner";

import { MetricTile } from "@/components/primitives/metric-tile";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  useMediaScanEvents,
  useMediaScanStatus,
  useResumeMediaScan,
} from "@/lib/hooks/use-media-scan";
import { MEDIA_TERMINAL_STAGES, type MediaScanRead } from "@/lib/types";

import { MediaScanEventList } from "./media-scan-event-list";
import { MediaScanStepper } from "./media-scan-stepper";

type MediaScanPanelProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accountId: string;
  scanId: string | null;
};

export function MediaScanPanel({ open, onOpenChange, accountId, scanId }: MediaScanPanelProps) {
  const queryClient = useQueryClient();
  const scanQuery = useMediaScanStatus(scanId ?? null);
  const eventsQuery = useMediaScanEvents(scanId ?? null, open);
  const resume = useResumeMediaScan();

  const scan = scanQuery.data ?? null;
  const isTerminal = scan ? MEDIA_TERMINAL_STAGES.has(scan.status) : false;

  const lastNotified = useRef<string | null>(null);
  useEffect(() => {
    if (!scan || !isTerminal) return;
    if (lastNotified.current === scan.id) return;
    lastNotified.current = scan.id;
    if (scan.status === "completed") {
      toast.success("Media scan complete", {
        description: "Conversation signals and score impact are ready.",
      });
      queryClient.invalidateQueries({ queryKey: ["account", accountId] });
      queryClient.invalidateQueries({ queryKey: ["conversation-signals", accountId] });
      queryClient.invalidateQueries({ queryKey: ["media-sources", accountId] });
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    } else if (scan.status === "failed") {
      toast.error("Media scan failed", { description: scan.last_error ?? undefined });
    }
  }, [scan, isTerminal, accountId, queryClient]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full border-l border-border/30 bg-surface/80 backdrop-blur-xl sm:max-w-[520px]"
      >
        <SheetHeader>
          <div className="flex items-start gap-3">
            <span className="grid size-8 shrink-0 place-items-center rounded-md border border-graph/20 bg-graph-soft/70 text-graph">
              <AudioLines className="size-4" aria-hidden />
            </span>
            <div className="flex-1">
              <SheetTitle className="text-[15px] tracking-[-0.01em]">Media scan</SheetTitle>
              <SheetDescription className="text-[11.5px] text-fg-muted">
                Discovers public conversations, transcribes, scrubs PII, and extracts spoken signals.
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto p-5">
          <PanelBody scan={scan} />

          <section className="mt-5 flex flex-col gap-2.5">
            <h3 className="flex items-center gap-2 text-[10.5px] font-semibold uppercase tracking-[0.05em] text-fg-secondary">
              <span className="h-px flex-1 bg-border/40" />
              Pipeline
              <span className="h-px flex-1 bg-border/40" />
            </h3>
            {scan ? (
              <MediaScanStepper status={scan.status} currentStage={scan.current_stage} />
            ) : null}
          </section>

          <section className="mt-5 flex flex-col gap-2.5">
            <h3 className="flex items-center gap-2 text-[10.5px] font-semibold uppercase tracking-[0.05em] text-fg-secondary">
              <span className="h-px flex-1 bg-border/40" />
              Event log
              <span className="h-px flex-1 bg-border/40" />
            </h3>
            <MediaScanEventList
              events={eventsQuery.data?.items ?? []}
              isLoading={eventsQuery.isLoading}
            />
          </section>
        </div>

        <div className="border-t border-border/30 bg-surface/50 px-5 py-3 backdrop-blur-sm">
          <div className="flex items-center justify-between gap-2">
            <span className="text-[10.5px] font-medium uppercase tracking-[0.04em] text-fg-muted">
              {scan ? `Mode · ${scan.mode}` : scanId ? "Connecting…" : "No scan running"}
            </span>
            <div className="flex items-center gap-2">
              {scan?.status === "failed" ? (
                <Button
                  variant="secondary"
                  size="sm"
                  className="border border-border/50"
                  loading={resume.isPending}
                  onClick={() => resume.mutate(scan.id)}
                >
                  <RotateCcw className="size-3.5" aria-hidden />
                  Resume
                </Button>
              ) : null}
              <Button
                variant="secondary"
                size="sm"
                className="border border-border/50"
                onClick={() => onOpenChange(false)}
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

function PanelBody({ scan }: { scan: MediaScanRead | null }) {
  if (!scan) {
    return (
      <p className="text-[13px] text-fg-secondary">
        Click <span className="font-semibold">Run Media Scan</span> to listen for public
        conversations about this account. The panel fills in stage by stage.
      </p>
    );
  }

  const counts = scan.counts ?? {
    sources_discovered: 0,
    sources_selected: 0,
    transcripts: 0,
    cache_hits: 0,
    conversation_signals: 0,
    memory_writes: 0,
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-3 gap-2">
        <MetricTile label="Sources" value={counts.sources_discovered} hint="discovered" />
        <MetricTile
          label="Transcripts"
          value={counts.transcripts}
          hint={`${counts.cache_hits} cached`}
        />
        <MetricTile label="Signals" value={counts.conversation_signals} hint="spoken" />
      </div>

      {scan.score_delta ? (
        <div className="flex items-center gap-2 rounded-[var(--radius-card)] border border-signal/30 bg-signal-soft/60 px-3 py-2 text-[12.5px] text-signal">
          <span className="font-semibold">Score impact · +{scan.score_delta}</span>
          <span className="opacity-80">from spoken evidence</span>
        </div>
      ) : null}

      {scan.status === "failed" ? (
        <div className="rounded-[var(--radius-card)] border border-risk/30 bg-risk-soft/60 px-3 py-2 text-[12px] text-risk">
          {scan.last_error ?? "The scan failed. You can resume from the last completed stage."}
        </div>
      ) : null}
    </div>
  );
}
