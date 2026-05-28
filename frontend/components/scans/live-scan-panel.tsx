"use client";

import { useQueryClient } from "@tanstack/react-query";
import { Radar } from "lucide-react";
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
      <SheetContent side="right" className="w-full sm:max-w-[520px]">
        <SheetHeader>
          <div className="flex items-start gap-3">
            <span className="grid size-8 shrink-0 place-items-center rounded-md bg-[color:var(--color-cobalt-soft)] text-[color:var(--color-cobalt)]">
              <Radar className="size-4" aria-hidden />
            </span>
            <div className="flex-1">
              <SheetTitle>Live scan</SheetTitle>
              <SheetDescription>
                Bright Data discovers public sources, AI/ML extracts signals, and Cognee writes
                memory.
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto p-5">
          <PanelBody scan={scan} />

          <section className="mt-5 flex flex-col gap-2">
            <h3 className="text-[11px] font-semibold tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
              Sources
            </h3>
            <ScanSourceStream
              sources={sourcesQuery.data ?? []}
              evidence={evidenceQuery.data ?? []}
              isLoading={sourcesQuery.isLoading}
            />
          </section>

          <section className="mt-5 flex flex-col gap-2">
            <h3 className="text-[11px] font-semibold tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
              Event log
            </h3>
            <ScanEventList events={eventsQuery.data?.items ?? []} isLoading={eventsQuery.isLoading} />
          </section>
        </div>

        <div className="border-t border-[color:var(--color-border-default)] px-5 py-3">
          <div className="flex items-center justify-between gap-2">
            <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-muted)]">
              {scan
                ? `Mode · ${scan.mode}`
                : scanId
                  ? "Connecting…"
                  : "No scan running"}
            </span>
            <Button variant="secondary" size="sm" onClick={() => onOpenChange(false)}>
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

      <div className="flex flex-wrap items-center gap-1.5">
        <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
          Integrations
        </span>
        <span className="inline-flex items-center gap-1 rounded-[var(--radius-chip)] border border-[color:color-mix(in_oklab,var(--color-cobalt)_25%,transparent)] bg-[color:var(--color-cobalt-soft)] px-1.5 py-0.5 text-[11px] text-[color:var(--color-cobalt)]">
          Bright Data · {counts.bright_data_calls}
        </span>
        <span className="inline-flex items-center gap-1 rounded-[var(--radius-chip)] border border-[color:color-mix(in_oklab,var(--color-cobalt)_25%,transparent)] bg-[color:var(--color-cobalt-soft)] px-1.5 py-0.5 text-[11px] text-[color:var(--color-cobalt)]">
          AI/ML · {counts.aiml_calls}
        </span>
        <span className="inline-flex items-center gap-1 rounded-[var(--radius-chip)] border border-[color:color-mix(in_oklab,var(--color-graph)_25%,transparent)] bg-[color:var(--color-graph-soft)] px-1.5 py-0.5 text-[11px] text-[color:var(--color-graph)]">
          Memory · {counts.memory_writes}
        </span>
      </div>

      {scan.status === "failed" ? (
        <div className="rounded-[var(--radius-card)] border border-[color:color-mix(in_oklab,var(--color-risk)_30%,transparent)] bg-[color:var(--color-risk-soft)] p-3 text-[12px] text-[color:var(--color-risk)]">
          {scan.error_message ?? "Scan failed."}
        </div>
      ) : null}

      {scan.status === "completed" ? (
        <div className="rounded-[var(--radius-card)] border border-[color:color-mix(in_oklab,var(--color-signal)_30%,transparent)] bg-[color:var(--color-signal-soft)] p-3 text-[12px] text-[color:var(--color-signal)]">
          Intelligence ready. The account brief and any sales-ready outreach drafts have been
          refreshed.
        </div>
      ) : null}
    </div>
  );
}
