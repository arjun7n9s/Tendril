"use client";

import { CheckCircle2, ExternalLink, OctagonX } from "lucide-react";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import type { EvidenceRead, SourceRead } from "@/lib/types";
import { cn } from "@/lib/utils/cn";

import { FetchMethodBadge } from "./fetch-method-badge";

type ScanSourceStreamProps = {
  sources: SourceRead[];
  evidence: EvidenceRead[];
  isLoading: boolean;
};

export function ScanSourceStream({ sources, evidence, isLoading }: ScanSourceStreamProps) {
  // Build a quick lookup: source URL -> evidence row, so we can show
  // fetch method + status as soon as the backend writes it.
  const byUrl = new Map<string, EvidenceRead>();
  for (const ev of evidence) byUrl.set(ev.url, ev);

  if (isLoading && sources.length === 0) {
    return (
      <div className="flex flex-col gap-1.5">
        {Array.from({ length: 4 }).map((_, idx) => (
          <Skeleton key={idx} className="h-9 rounded-[6px]" />
        ))}
      </div>
    );
  }

  if (sources.length === 0) {
    return (
      <p className="text-[12px] text-[color:var(--color-fg-muted)]">
        Sources will appear as Bright Data discovers public pages for this account.
      </p>
    );
  }

  return (
    <ScrollArea className="max-h-[280px]">
      <ul className="flex flex-col gap-1">
        {sources.map((source) => {
          const ev = byUrl.get(source.url);
          const status = ev?.fetch_status;
          let host = source.url;
          try {
            host = new URL(source.url).hostname.replace(/^www\./, "");
          } catch {
            /* keep original */
          }
          return (
            <li
              key={source.id}
              className={cn(
                "flex items-center justify-between gap-2 rounded-[var(--radius-chip)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] px-2 py-1.5 text-[12px]",
              )}
            >
              <div className="flex min-w-0 items-center gap-2">
                {status === "success" ? (
                  <CheckCircle2
                    className="size-3.5 shrink-0 text-[color:var(--color-signal)]"
                    aria-hidden
                  />
                ) : status === "failed" ? (
                  <OctagonX
                    className="size-3.5 shrink-0 text-[color:var(--color-risk)]"
                    aria-hidden
                  />
                ) : (
                  <span
                    className="size-1.5 shrink-0 rounded-full bg-[color:var(--color-fg-muted)]"
                    aria-hidden
                  />
                )}
                <span className="min-w-0 truncate font-medium text-[color:var(--color-fg-primary)]">
                  {host}
                </span>
                <span className="hidden text-[color:var(--color-fg-muted)] md:inline">
                  · rank {source.rank}
                </span>
              </div>
              <div className="flex shrink-0 items-center gap-1.5">
                {ev ? <FetchMethodBadge method={ev.fetch_method} /> : null}
                <a
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[color:var(--color-fg-muted)] hover:text-[color:var(--color-fg-primary)]"
                  aria-label={`Open ${host}`}
                >
                  <ExternalLink className="size-3" aria-hidden />
                </a>
              </div>
            </li>
          );
        })}
      </ul>
    </ScrollArea>
  );
}
