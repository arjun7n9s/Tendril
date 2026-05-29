"use client";

import {
  AlertTriangle,
  Brain,
  Database,
  Info,
  type LucideIcon,
  Mic,
  OctagonX,
  Radar,
  Recycle,
  ShieldAlert,
  Sparkles,
  Zap,
} from "lucide-react";

import { ScrollArea } from "@/components/ui/scroll-area";
import type { MediaScanEventRead, MediaScanEventType } from "@/lib/types";
import { cn } from "@/lib/utils/cn";

const EVENT_META: Record<
  MediaScanEventType,
  { icon: LucideIcon; tone: "neutral" | "info" | "ok" | "warn" | "error" | "graph" }
> = {
  stage_started: { icon: Radar, tone: "info" },
  stage_completed: { icon: Sparkles, tone: "ok" },
  stage_skipped: { icon: Recycle, tone: "neutral" },
  bright_data_call: { icon: Radar, tone: "info" },
  featherless_call: { icon: Zap, tone: "info" },
  aiml_call: { icon: Brain, tone: "info" },
  speechmatics_call: { icon: Mic, tone: "graph" },
  cache_hit: { icon: Recycle, tone: "ok" },
  memory_write: { icon: Database, tone: "graph" },
  pii_redaction: { icon: ShieldAlert, tone: "warn" },
  notification: { icon: Info, tone: "info" },
  warning: { icon: AlertTriangle, tone: "warn" },
  error: { icon: OctagonX, tone: "error" },
  info: { icon: Info, tone: "neutral" },
};

const TONE_CLASS = {
  neutral: "text-[color:var(--color-fg-muted)]",
  info: "text-[color:var(--color-cobalt)]",
  ok: "text-[color:var(--color-signal)]",
  warn: "text-[color:var(--color-evidence)]",
  error: "text-[color:var(--color-risk)]",
  graph: "text-[color:var(--color-graph)]",
} as const;

export function MediaScanEventList({
  events,
  isLoading,
}: {
  events: MediaScanEventRead[];
  isLoading: boolean;
}) {
  if (isLoading && events.length === 0) {
    return <p className="text-[12px] text-fg-muted">Loading events…</p>;
  }
  if (events.length === 0) {
    return <p className="text-[12px] text-fg-muted">No events yet.</p>;
  }

  return (
    <ScrollArea className="max-h-[260px]">
      <ol className="flex flex-col">
        {events.map((event) => {
          const meta = EVENT_META[event.event_type] ?? EVENT_META.info;
          const Icon = meta.icon;
          return (
            <li
              key={event.id}
              className="flex items-start gap-2 border-b border-border-default py-1.5 text-[12px] leading-snug last:border-b-0"
            >
              <Icon className={cn("mt-0.5 size-3.5 shrink-0", TONE_CLASS[meta.tone])} aria-hidden />
              <div className="flex min-w-0 flex-1 flex-col">
                <span className="text-fg-primary">{event.message}</span>
                <span className="text-[10px] uppercase tracking-[0.04em] text-fg-muted">
                  #{event.sequence}
                  {event.stage ? ` · ${event.stage}` : null}
                </span>
              </div>
            </li>
          );
        })}
      </ol>
    </ScrollArea>
  );
}
