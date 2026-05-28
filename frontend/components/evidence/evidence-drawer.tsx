"use client";

import { useQuery } from "@tanstack/react-query";
import { ExternalLink } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
      <SheetContent side="right" className="w-full sm:max-w-[560px]">
        <SheetHeader>
          <div className="flex items-start justify-between gap-3">
            <div className="flex flex-col gap-1">
              <SheetTitle>{COPY.evidence.drawerTitle}</SheetTitle>
              <SheetDescription>
                Public source evidence used to support this signal.
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-5 py-4">
          <header className="flex flex-col gap-2">
            <h3 className="text-[14px] leading-snug font-semibold text-[color:var(--color-fg-primary)]">
              {title || "Untitled source"}
            </h3>
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 break-all text-[12px] text-[color:var(--color-fg-secondary)] hover:text-[color:var(--color-fg-primary)]"
            >
              {host}
              <ExternalLink className="size-3" aria-hidden />
            </a>
          </header>

          <div className="flex flex-wrap items-center gap-1.5">
            {evidence?.fetch_method ? (
              <span className="inline-flex items-center gap-1 text-[11px] text-[color:var(--color-fg-secondary)]">
                {COPY.evidence.fetchedVia}
                <FetchMethodBadge method={evidence.fetch_method} />
              </span>
            ) : null}
            {evidence?.fetched_at ? (
              <span
                className="text-[11px] text-[color:var(--color-fg-muted)]"
                title={formatAbsolute(evidence.fetched_at)}
              >
                {formatRelative(evidence.fetched_at)}
              </span>
            ) : null}
            {evidence?.http_status ? (
              <Badge variant="outline" size="sm">
                HTTP {evidence.http_status}
              </Badge>
            ) : null}
          </div>

          {subject?.kind === "signal" ? (
            <section className="flex flex-col gap-2 rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-canvas)] p-3">
              <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
                Signal
              </span>
              {subject.signal.fact_text ? (
                <p className="text-[13px] leading-relaxed text-[color:var(--color-fg-primary)]">
                  {subject.signal.fact_text}
                </p>
              ) : null}
              {subject.signal.inference_text ? (
                <p className="text-[12px] leading-relaxed text-[color:var(--color-fg-secondary)]">
                  <span className="font-medium text-[color:var(--color-evidence)]">Inference. </span>
                  {subject.signal.inference_text}
                </p>
              ) : null}
            </section>
          ) : null}

          <section className="flex flex-col gap-2">
            <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
              Source content
            </span>
            <ScrollArea className="max-h-[420px] rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] p-3">
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
                <p className="text-[12px] text-[color:var(--color-fg-muted)]">
                  No cached content. Open the original source for the full page.
                </p>
              )}
            </ScrollArea>
          </section>
        </div>

        <SheetFooter>
          <div className="flex w-full items-center justify-between gap-2">
            <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-muted)]">
              {evidence?.fetch_status === "failed" ? "Fetch failed" : "Read-only preview"}
            </span>
            <div className="flex items-center gap-2">
              <Button asChild variant="secondary" size="sm">
                <a href={url} target="_blank" rel="noreferrer">
                  <span>{COPY.evidence.openOriginal}</span>
                </a>
              </Button>
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
