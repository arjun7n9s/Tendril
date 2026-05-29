"use client";

import {
  CalendarClock,
  ExternalLink,
  Mic2,
  type LucideIcon,
  PlayCircle,
  Presentation,
  Radio,
  TrendingUp,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { MediaSourceRead, MediaSourceStatus, MediaSourceType } from "@/lib/types";
import { formatRelative } from "@/lib/utils/dates";
import { formatDuration } from "@/lib/utils/timecode";

const TYPE_ICON: Record<MediaSourceType, LucideIcon> = {
  youtube: PlayCircle,
  podcast: Radio,
  earnings_call: TrendingUp,
  webinar: Presentation,
  conference: Users,
  interview: Mic2,
  other: Mic2,
};

const TYPE_LABEL: Record<MediaSourceType, string> = {
  youtube: "YouTube",
  podcast: "Podcast",
  earnings_call: "Earnings call",
  webinar: "Webinar",
  conference: "Conference",
  interview: "Interview",
  other: "Source",
};

const STATUS_VARIANT: Record<
  MediaSourceStatus,
  "neutral" | "cobalt" | "signal" | "evidence" | "risk"
> = {
  discovered: "neutral",
  ranked: "cobalt",
  selected: "cobalt",
  skipped: "neutral",
  resolved: "evidence",
  transcribed: "evidence",
  extracted: "signal",
  failed: "risk",
};

export function MediaSourceList({ sources }: { sources: MediaSourceRead[] }) {
  if (sources.length === 0) {
    return <p className="text-[12px] text-fg-muted">No media sources discovered yet.</p>;
  }

  return (
    <ul className="flex flex-col gap-2.5">
      {sources.map((src) => {
        const Icon = TYPE_ICON[src.source_type];
        const host = (() => {
          try {
            return new URL(src.source_url).hostname.replace(/^www\./, "");
          } catch {
            return src.source_url;
          }
        })();
        return (
          <li
            key={src.id}
            className="flex flex-col gap-2 rounded-[var(--radius-card)] border border-border bg-surface p-3.5"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-2.5">
                <span className="grid size-7 shrink-0 place-items-center rounded-md border border-border bg-raised text-fg-secondary">
                  <Icon className="size-3.5" aria-hidden />
                </span>
                <div className="flex flex-col gap-1">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <Badge variant="neutral" size="sm" className="font-semibold">
                      {TYPE_LABEL[src.source_type]}
                    </Badge>
                    <Badge variant={STATUS_VARIANT[src.status]} size="sm" className="font-semibold">
                      {src.status}
                    </Badge>
                    {src.rank_score != null ? (
                      <span className="text-[10.5px] font-medium text-fg-muted">
                        rank {Math.round(src.rank_score * 100)}
                      </span>
                    ) : null}
                  </div>
                  <h4 className="text-[13px] font-semibold leading-snug text-fg-primary">
                    {src.title ?? host}
                  </h4>
                </div>
              </div>
              <a
                href={src.source_url}
                target="_blank"
                rel="noreferrer"
                className="text-fg-muted transition-colors hover:text-fg-primary"
                aria-label="Open source"
              >
                <ExternalLink className="size-3.5" aria-hidden />
              </a>
            </div>

            {src.rank_reason ? (
              <p className="text-[11.5px] leading-relaxed text-fg-secondary">{src.rank_reason}</p>
            ) : null}

            <div className="flex flex-wrap items-center gap-3 text-[10.5px] text-fg-muted">
              {src.publisher ? <span>{src.publisher}</span> : null}
              {src.duration_seconds ? (
                <span className="inline-flex items-center gap-1">
                  <PlayCircle className="size-3" aria-hidden />
                  {formatDuration(src.duration_seconds)}
                </span>
              ) : null}
              {src.published_at ? (
                <span className="inline-flex items-center gap-1">
                  <CalendarClock className="size-3" aria-hidden />
                  {formatRelative(src.published_at)}
                </span>
              ) : null}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
