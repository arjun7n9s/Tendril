"use client";

import { useQueryClient } from "@tanstack/react-query";
import { motion, useReducedMotion } from "framer-motion";
import { Radar } from "lucide-react";
import { useEffect, useRef } from "react";
import { toast } from "sonner";

import {
  ScanCompleteIllustration,
  ScanFailedIllustration,
} from "@/components/illustrations";
import { MetricTile } from "@/components/primitives/metric-tile";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { COPY } from "@/lib/copy";
import {
  useScanEvents,
  useScanEvidence,
  useScanSources,
  useScanStatus,
} from "@/lib/hooks/use-scan";
import type { ScanRead } from "@/lib/types";
import { TERMINAL_SCAN_STATUSES } from "@/lib/types";

import { ScanEventList } from "./scan-event-list";
import { ScanPhaseStepper } from "./scan-phase-stepper";
import { ScanSourceStream } from "./scan-source-stream";

type LiveScanPanelProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accountId: string;
  scanId: string | null;
};

export function LiveScanPanel({ open, onOpenChange, accountId, scanId }: LiveScanPanelProps) {
  const queryClient = useQueryClient();

  const scanQuery = useScanStatus(scanId ?? null);
  const eventsQuery = useScanEvents(scanId ?? null, 0, open);
  const sourcesQuery = useScanSources(scanId ?? null, open);
  const evidenceQuery = useScanEvidence(scanId ?? null, open);

  const scan = scanQuery.data ?? null;
  const isTerminal = scan ? TERMINAL_SCAN_STATUSES.has(scan.status) : false;

  // Fire completion / failure side-effects exactly once per scan id.
  const lastNotifiedScan = useRef<string | null>(null);
  useEffect(() => {
    if (!scan || !isTerminal) return;
    if (lastNotifiedScan.current === scan.id) return;
    lastNotifiedScan.current = scan.id;
    if (scan.status === "completed") {
      toast.success(COPY.scan.completionToast);
      queryClient.invalidateQueries({ queryKey: ["account", accountId] });
      queryClient.invalidateQueries({ queryKey: ["account-signals", accountId] });
      queryClient.invalidateQueries({ queryKey: ["outreach-pending"] });
    } else if (scan.status === "failed") {
      toast.error(COPY.scan.failureToast, {
        description: scan.error_message ?? undefined,
      });
    }
  }, [scan, isTerminal, accountId, queryClient]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-[520px] bg-surface/80 backdrop-blur-xl border-l border-border/30">
        <SheetHeader>
          <div className="flex items-start gap-3">
            <span className="relative grid size-8 shrink-0 place-items-center rounded-md bg-cobalt-soft/70 text-cobalt border border-cobalt/20">
              <Radar className="size-4 animate-[spin_8s_linear_infinite]" aria-hidden />
              <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-cobalt shadow-[0_0_6px_rgba(52,87,213,0.6)] animate-pulse" />
            </span>
            <div className="flex-1">
              <SheetTitle className="text-[15px] tracking-[-0.01em]">Live scan</SheetTitle>
              <SheetDescription className="text-[11.5px] text-fg-muted">
                Bright Data discovers public sources, AI/ML extracts signals, and Cognee writes
                memory.
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto p-5">
          <PanelBody scan={scan} />

          <section className="mt-5 flex flex-col gap-2.5">
            <h3 className="text-[10.5px] font-semibold tracking-[0.05em] uppercase text-fg-secondary flex items-center gap-2">
              <span className="h-px flex-1 bg-border/40" />
              Sources
              <span className="h-px flex-1 bg-border/40" />
            </h3>
            <ScanSourceStream
              sources={sourcesQuery.data ?? []}
              evidence={evidenceQuery.data ?? []}
              isLoading={sourcesQuery.isLoading}
            />
          </section>

          <section className="mt-5 flex flex-col gap-2.5">
            <h3 className="text-[10.5px] font-semibold tracking-[0.05em] uppercase text-fg-secondary flex items-center gap-2">
              <span className="h-px flex-1 bg-border/40" />
              Event log
              <span className="h-px flex-1 bg-border/40" />
            </h3>
            <ScanEventList events={eventsQuery.data?.items ?? []} isLoading={eventsQuery.isLoading} />
          </section>
        </div>

        <div className="border-t border-border/30 bg-surface/50 px-5 py-3 backdrop-blur-sm">
          <div className="flex items-center justify-between gap-2">
            <span className="text-[10.5px] font-medium tracking-[0.04em] uppercase text-fg-muted">
              {scan
                ? `Mode · ${scan.mode}`
                : scanId
                  ? "Connecting…"
                  : "No scan running"}
            </span>
            <Button variant="secondary" size="sm" className="border border-border/50 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200" onClick={() => onOpenChange(false)}>
              Close
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

function PanelBody({ scan }: { scan: ScanRead | null }) {
  if (!scan) {
    return (
      <div className="flex flex-col gap-3">
        <p className="text-[13px] text-[color:var(--color-fg-secondary)]">
          Click <span className="font-semibold">Run Live Scan</span> to start a Bright Data scan
          for this account. The panel will populate phase-by-phase as evidence is fetched.
        </p>
      </div>
    );
  }

  const counts = scan.counts ?? {
    discovered: 0,
    selected: 0,
    fetched: 0,
    failed: 0,
    signals: 0,
    bright_data_calls: 0,
    aiml_calls: 0,
    memory_writes: 0,
  };

  return (
    <div className="flex flex-col gap-4">
      <ScanPhaseStepper status={scan.status} />

      <div className="grid grid-cols-3 gap-2">
        <MetricTile label="Discovered" value={counts.discovered} hint="sources found" />
        <MetricTile label="Fetched" value={counts.fetched} hint={`${counts.failed} failed`} />
        <MetricTile label="Signals" value={counts.signals} hint="extracted" />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[10.5px] font-semibold tracking-[0.05em] uppercase text-fg-secondary">
          Pipelines
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-[var(--radius-chip)] border border-cobalt/20 bg-cobalt-soft/60 px-2 py-0.5 text-[11px] font-medium text-cobalt transition-all duration-300 hover:border-cobalt/40 hover:shadow-glow-cobalt">
          <span className="relative flex h-1.5 w-1.5 shrink-0"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cobalt opacity-60"></span><span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-cobalt"></span></span>
          Bright Data · {counts.bright_data_calls}
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-[var(--radius-chip)] border border-cobalt/20 bg-cobalt-soft/60 px-2 py-0.5 text-[11px] font-medium text-cobalt transition-all duration-300 hover:border-cobalt/40 hover:shadow-glow-cobalt">
          <span className="relative flex h-1.5 w-1.5 shrink-0"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cobalt opacity-60"></span><span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-cobalt"></span></span>
          AI/ML · {counts.aiml_calls}
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-[var(--radius-chip)] border border-graph/20 bg-graph-soft/60 px-2 py-0.5 text-[11px] font-medium text-graph transition-all duration-300 hover:border-graph/40">
          <span className="relative flex h-1.5 w-1.5 shrink-0"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-graph opacity-60"></span><span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-graph"></span></span>
          Memory · {counts.memory_writes}
        </span>
      </div>

      {scan.status === "failed" ? (
        <ResultBanner tone="risk">
          <ScanFailedIllustration className="size-10" />
          <div>
            <div className="text-[13px] font-semibold">Scan failed</div>
            <p className="text-[12px] opacity-90">
              {scan.error_message ?? "Try running the scan again."}
            </p>
          </div>
        </ResultBanner>
      ) : null}

      {scan.status === "completed" ? (
        <ResultBanner tone="signal">
          <ScanCompleteIllustration className="size-10" />
          <div>
            <div className="text-[13px] font-semibold">Intelligence ready</div>
            <p className="text-[12px] opacity-90">
              The account brief and any sales-ready outreach drafts have been refreshed.
            </p>
          </div>
        </ResultBanner>
      ) : null}
    </div>
  );
}

function ResultBanner({
  tone,
  children,
}: {
  tone: "signal" | "risk";
  children: React.ReactNode;
}) {
  const reduce = useReducedMotion();
  const palette =
    tone === "signal"
      ? "border-signal/30 bg-signal-soft/70 text-signal shadow-glow-emerald"
      : "border-risk/30 bg-risk-soft/70 text-risk";
  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 8, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        type: "spring",
        stiffness: 280,
        damping: 24,
        mass: 0.5,
      }}
      className={`flex items-center gap-3 rounded-[var(--radius-card)] border p-4 backdrop-blur-sm ${palette}`}
    >
      {children}
    </motion.div>
  );
}
