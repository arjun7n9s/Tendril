"use client";

import { useQuery } from "@tanstack/react-query";
import { ExternalLink } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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
import { scansApi } from "@/lib/api";
import { COPY } from "@/lib/copy";
import type { EvidenceRead, SignalRead } from "@/lib/types";
import { formatAbsolute, formatRelative } from "@/lib/utils/dates";

import { FetchMethodBadge } from "@/components/scans/fetch-method-badge";

type DrawerSubject =
  | { kind: "signal"; signal: SignalRead; scanId?: string | null }
  | { kind: "evidence"; evidence: EvidenceRead };

type EvidenceDrawerProps = {
  subject: DrawerSubject | null;
  onOpenChange: (open: boolean) => void;
};

export function EvidenceDrawer({ subject, onOpenChange }: EvidenceDrawerProps) {
  const open = subject !== null;
  const scanId =
    subject?.kind === "signal"
      ? (subject.scanId ?? subject.signal.scan_id)
      : subject?.kind === "evidence"
        ? subject.evidence.scan_id
        : null;

  // Fetch the full evidence list once per scan; we then resolve the
  // matching row by signal.evidence_document_id or evidence.id. This
  // is cheaper than threading every evidence document down through
  // signals and keeps the drawer self-contained.
  const evidenceQuery = useQuery({
    queryKey: ["scan-evidence", scanId],
    queryFn: ({ signal }) => scansApi.getScanEvidence(scanId!, signal),
    enabled: open && Boolean(scanId),
  });

  let evidence: EvidenceRead | null = null;
  let title = "";
  let url = "";

  if (subject?.kind === "signal") {
    const targetId = subject.signal.evidence_document_id;
    evidence = (evidenceQuery.data ?? []).find((e) => e.id === targetId) ?? null;
    title = subject.signal.title;
    url = subject.signal.evidence_url;
  } else if (subject?.kind === "evidence") {
    evidence = subject.evidence;
    title = evidence.title ?? evidence.url;
    url = evidence.url;
  }

  const host = (() => {
    try {
      return new URL(url).hostname.replace(/^www\./, "");
    } catch {
      return url;
    }
  })();

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-[560px] bg-surface/80 backdrop-blur-xl border-l border-border/30">
        <SheetHeader>
          <div className="flex items-start justify-between gap-3">
            <div className="flex flex-col gap-1">
              <SheetTitle className="text-[15px] tracking-[-0.01em]">{COPY.evidence.drawerTitle}</SheetTitle>
              <SheetDescription className="text-[11.5px] text-fg-muted">
                Public source evidence used to support this signal.
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-5 py-4">
          <header className="flex flex-col gap-2">
            <h3 className="text-[14px] leading-snug font-semibold text-fg-primary tracking-[-0.01em]">
              {title || "Untitled source"}
            </h3>
            <div className="flex flex-wrap items-center gap-2">
              <a
                href={url}
                target="_blank"
                rel="noreferrer"
                className="group/link inline-flex items-center gap-1.5 break-all text-[12px] text-fg-secondary transition-colors hover:text-fg-primary"
              >
                {host}
                <ExternalLink className="size-3 opacity-0 -translate-x-0.5 translate-y-0.5 transition-all duration-200 group-hover/link:opacity-100 group-hover/link:translate-x-0 group-hover/link:translate-y-0" aria-hidden />
              </a>
              {url ? <CopyButton value={url} label="Copy URL" /> : null}
            </div>
          </header>

          <div className="flex flex-wrap items-center gap-2">
            {evidence?.fetch_method ? (
              <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-fg-secondary">
                {COPY.evidence.fetchedVia}
                <FetchMethodBadge method={evidence.fetch_method} />
              </span>
            ) : null}
            {evidence?.fetched_at ? (
              <span
                className="text-[11px] text-fg-muted tabular-nums"
                title={formatAbsolute(evidence.fetched_at)}
              >
                {formatRelative(evidence.fetched_at)}
              </span>
            ) : null}
            {evidence?.http_status ? (
              <Badge variant="outline" size="sm" className="font-semibold">
                HTTP {evidence.http_status}
              </Badge>
            ) : null}
          </div>

          {subject?.kind === "signal" ? (
            <section className="flex flex-col gap-2 rounded-[var(--radius-card)] border border-border/40 bg-canvas/70 p-3.5 backdrop-blur-sm">
              <span className="text-[10.5px] font-semibold tracking-[0.05em] uppercase text-fg-secondary">
                Signal
              </span>
              {subject.signal.fact_text ? (
                <p className="text-[13px] leading-relaxed text-fg-primary">
                  {subject.signal.fact_text}
                </p>
              ) : null}
              {subject.signal.inference_text ? (
                <p className="text-[12px] leading-relaxed text-fg-secondary">
                  <span className="font-semibold text-evidence">Inference · </span>
                  {subject.signal.inference_text}
                </p>
              ) : null}
            </section>
          ) : null}

          <section className="flex flex-col gap-2.5">
            <span className="text-[10.5px] font-semibold tracking-[0.05em] uppercase text-fg-secondary flex items-center gap-2">
              <span className="h-px flex-1 bg-border/40" />
              Source content
              <span className="h-px flex-1 bg-border/40" />
            </span>
            <ScrollArea className="max-h-[420px] rounded-[var(--radius-card)] border border-border/40 bg-surface/60 p-4 backdrop-blur-sm">
              {evidenceQuery.isLoading && !evidence ? (
                <div className="flex flex-col gap-2">
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-5/6" />
                  <Skeleton className="h-3 w-4/6" />
                </div>
              ) : evidence?.content_markdown ? (
                <div className="prose-evidence prose-sm max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {evidence.content_markdown}
                  </ReactMarkdown>
                </div>
              ) : (
                <p className="text-[12px] text-fg-muted">
                  No cached content. Open the original source for the full page.
                </p>
              )}
            </ScrollArea>
          </section>
        </div>

        <SheetFooter>
          <div className="flex w-full items-center justify-between gap-2">
            <span className="text-[10.5px] font-medium tracking-[0.04em] uppercase text-fg-muted">
              {evidence?.fetch_status === "failed" ? "Fetch failed" : "Read-only preview"}
            </span>
            <div className="flex items-center gap-2">
              <Button asChild variant="secondary" size="sm" className="border border-border/50 font-semibold hover:scale-[1.02] active:scale-[0.98] transition-all duration-200">
                <a href={url} target="_blank" rel="noreferrer">
                  <span>{COPY.evidence.openOriginal}</span>
                </a>
              </Button>
              <Button variant="ghost" size="sm" className="hover:scale-[1.02] active:scale-[0.98] transition-all duration-200" onClick={() => onOpenChange(false)}>
                Close
              </Button>
            </div>
          </div>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
