"use client";

import { useQuery } from "@tanstack/react-query";
import { Copy, ExternalLink, Quote, ShieldCheck, ShieldAlert, ShieldX } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CopyButton } from "@/components/primitives/copy-button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { mediaApi } from "@/lib/api";
import type { ConversationSignalRead, PrivacyStatus } from "@/lib/types";
import { cn } from "@/lib/utils/cn";
import { formatTimecode } from "@/lib/utils/timecode";

import { QuoteWaveform } from "./quote-waveform";

type ConversationEvidenceDrawerProps = {
  signal: ConversationSignalRead | null;
  onOpenChange: (open: boolean) => void;
};

const PRIVACY_META: Record<
  PrivacyStatus,
  { label: string; icon: typeof ShieldCheck; variant: "signal" | "evidence" | "risk" }
> = {
  clean: { label: "Clean", icon: ShieldCheck, variant: "signal" },
  scrubbed: { label: "PII scrubbed", icon: ShieldAlert, variant: "evidence" },
  sensitive_blocked: { label: "Sensitive · blocked", icon: ShieldX, variant: "risk" },
};

function countRedactions(findings: Record<string, number> | null | undefined): number {
  if (!findings) return 0;
  return Object.values(findings).reduce((sum, n) => sum + (Number(n) || 0), 0);
}

export function ConversationEvidenceDrawer({
  signal,
  onOpenChange,
}: ConversationEvidenceDrawerProps) {
  const open = signal !== null;
  const transcriptId = signal?.transcript_id ?? null;
  const [copied, setCopied] = useState(false);

  const transcriptQuery = useQuery({
    queryKey: ["transcript", transcriptId],
    queryFn: ({ signal: abort }) => mediaApi.getTranscript(transcriptId!, abort),
    enabled: open && Boolean(transcriptId),
  });

  const host = (() => {
    if (!signal?.source_url) return "";
    try {
      return new URL(signal.source_url).hostname.replace(/^www\./, "");
    } catch {
      return signal.source_url;
    }
  })();

  const privacy = signal ? PRIVACY_META[signal.privacy_status] : null;
  const PrivacyIcon = privacy?.icon;
  const redactionCount = countRedactions(
    transcriptQuery.data?.pii_findings_json as Record<string, number> | null | undefined,
  );

  const copyCitation = async () => {
    if (!signal) return;
    const ts = signal.quote_start_seconds != null ? ` (${formatTimecode(signal.quote_start_seconds)})` : "";
    const speaker = signal.speaker_label ? `${signal.speaker_label}, ` : "";
    const citation = `"${signal.quote_text ?? signal.title}" — ${speaker}${host}${ts}\n${signal.source_url}`;
    try {
      await navigator.clipboard.writeText(citation);
      setCopied(true);
      toast.success("Quote + citation copied");
      setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error("Could not copy");
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full border-l border-border bg-surface sm:max-w-[560px]"
      >
        <SheetHeader>
          <div className="flex flex-col gap-1">
            <SheetTitle className="text-[15px] tracking-[-0.01em]">Conversation evidence</SheetTitle>
            <SheetDescription className="text-[11.5px] text-fg-muted">
              A timestamped quote from a public spoken source, with its scrubbed transcript.
            </SheetDescription>
          </div>
        </SheetHeader>

        {signal ? (
          <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-5 py-4">
            <header className="flex flex-col gap-2">
              <h3 className="text-[14px] font-semibold leading-snug tracking-[-0.01em] text-fg-primary">
                {signal.title}
              </h3>
              <div className="flex flex-wrap items-center gap-2">
                <a
                  href={signal.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="group/link inline-flex items-center gap-1.5 break-all text-[12px] text-fg-secondary transition-colors hover:text-fg-primary"
                >
                  {host}
                  <ExternalLink className="size-3 opacity-60" aria-hidden />
                </a>
                {signal.source_url ? <CopyButton value={signal.source_url} label="Copy URL" /> : null}
                {privacy && PrivacyIcon ? (
                  <Badge variant={privacy.variant} size="sm" className="gap-1 font-semibold">
                    <PrivacyIcon className="size-3" aria-hidden />
                    {privacy.label}
                  </Badge>
                ) : null}
              </div>
            </header>

            {/* Waveform locating the quote in the recording */}
            <section className="rounded-[var(--radius-card)] border border-border/40 bg-canvas/60 p-3">
              <QuoteWaveform
                durationSeconds={signal.quote_end_seconds ? signal.quote_end_seconds * 1.4 : null}
                quoteStart={signal.quote_start_seconds}
                quoteEnd={signal.quote_end_seconds}
                seed={signal.id}
              />
            </section>

            {/* The quote */}
            <section className="flex flex-col gap-2 rounded-[var(--radius-card)] border border-evidence/30 bg-evidence-soft/40 p-3.5">
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center gap-1.5 text-[10.5px] font-semibold uppercase tracking-[0.05em] text-evidence">
                  <Quote className="size-3" aria-hidden />
                  {signal.speaker_label ?? "Speaker"}
                </span>
                <span className="font-mono text-[11px] tabular-nums text-fg-muted">
                  {formatTimecode(signal.quote_start_seconds)}
                  {signal.quote_end_seconds != null
                    ? ` – ${formatTimecode(signal.quote_end_seconds)}`
                    : ""}
                </span>
              </div>
              {signal.quote_text ? (
                <blockquote className="text-[13px] leading-relaxed text-fg-primary">
                  “{signal.quote_text}”
                </blockquote>
              ) : (
                <p className="text-[12px] text-fg-muted">No quote captured.</p>
              )}
              <div className="flex justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 gap-1 px-1.5 text-[11px]"
                  onClick={copyCitation}
                >
                  <Copy className="size-3" aria-hidden />
                  {copied ? "Copied" : "Copy quote + citation"}
                </Button>
              </div>
            </section>

            {signal.fact_text ? (
              <section className="flex flex-col gap-1">
                <span className="text-[10.5px] font-semibold uppercase tracking-[0.05em] text-fg-secondary">
                  Fact
                </span>
                <p className="text-[13px] leading-relaxed text-fg-primary">{signal.fact_text}</p>
              </section>
            ) : null}

            {signal.inference_text ? (
              <section className="flex flex-col gap-1">
                <span className="text-[10.5px] font-semibold uppercase tracking-[0.05em] text-fg-secondary">
                  Inference
                </span>
                <p className="text-[12px] leading-relaxed text-fg-secondary">
                  {signal.inference_text}
                </p>
              </section>
            ) : null}

            {signal.recommended_action ? (
              <section className="flex items-start gap-2 rounded-[var(--radius-chip)] border border-border bg-canvas px-3 py-2 text-[12px] leading-normal text-fg-secondary">
                <span className="select-none font-semibold text-fg-primary">Next steps:</span>
                <span>{signal.recommended_action}</span>
              </section>
            ) : null}

            {/* Transcript excerpt */}
            <section className="flex flex-col gap-2.5">
              <div className="flex items-center justify-between gap-2">
                <span className="flex flex-1 items-center gap-2 text-[10.5px] font-semibold uppercase tracking-[0.05em] text-fg-secondary">
                  <span className="h-px flex-1 bg-border/40" />
                  Scrubbed transcript
                  <span className="h-px flex-1 bg-border/40" />
                </span>
              </div>
              {redactionCount > 0 ? (
                <p className="inline-flex items-center gap-1.5 rounded-[var(--radius-chip)] border border-evidence/25 bg-evidence-soft/40 px-2 py-1 text-[11px] text-evidence">
                  <ShieldAlert className="size-3" aria-hidden />
                  {redactionCount} identifier{redactionCount === 1 ? "" : "s"} redacted before this
                  was stored — outreach never sees raw personal data.
                </p>
              ) : null}
              <ScrollArea className="max-h-[300px] rounded-[var(--radius-card)] border border-border/40 bg-surface/60 p-4">
                {transcriptQuery.isLoading ? (
                  <div className="flex flex-col gap-2">
                    <Skeleton className="h-3 w-full" />
                    <Skeleton className="h-3 w-5/6" />
                    <Skeleton className="h-3 w-4/6" />
                  </div>
                ) : transcriptQuery.data?.segments_json?.length ? (
                  <ol className="flex flex-col gap-2.5">
                    {transcriptQuery.data.segments_json.map((seg, idx) => {
                      const isQuote =
                        signal.quote_start_seconds != null &&
                        seg.start != null &&
                        Math.abs(seg.start - signal.quote_start_seconds) < 0.5;
                      return (
                        <li
                          key={idx}
                          className={cn(
                            "flex flex-col gap-0.5 rounded-md px-2 py-1.5 text-[12px] leading-relaxed",
                            isQuote
                              ? "bg-evidence-soft/50 ring-1 ring-evidence/30"
                              : "text-fg-secondary",
                          )}
                        >
                          <span className="flex items-center gap-2 text-[10px] uppercase tracking-[0.04em] text-fg-muted">
                            <span className="font-mono tabular-nums">
                              {formatTimecode(seg.start)}
                            </span>
                            {seg.speaker ? <span>{seg.speaker}</span> : null}
                          </span>
                          <span className={isQuote ? "text-fg-primary" : undefined}>
                            {seg.text}
                          </span>
                        </li>
                      );
                    })}
                  </ol>
                ) : (
                  <p className="text-[12px] text-fg-muted">
                    Transcript unavailable. Open the original source for the full conversation.
                  </p>
                )}
              </ScrollArea>
            </section>
          </div>
        ) : null}

        <SheetFooter>
          <div className="flex w-full items-center justify-between gap-2">
            <span className="text-[10.5px] font-medium uppercase tracking-[0.04em] text-fg-muted">
              Read-only · scrubbed for outreach safety
            </span>
            <div className="flex items-center gap-2">
              {signal?.source_url ? (
                <Button
                  asChild
                  variant="secondary"
                  size="sm"
                  className="border border-border/50 font-semibold"
                >
                  <a href={signal.source_url} target="_blank" rel="noreferrer">
                    Open source
                  </a>
                </Button>
              ) : null}
              <Button variant="ghost" size="sm" onClick={() => onOpenChange(false)}>
                Close
              </Button>
            </div>
          </div>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
