"use client";

import {
  AlertTriangle,
  Brain,
  Database,
  Info,
  OctagonX,
  Radar,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

import { ScrollArea } from "@/components/ui/scroll-area";
import type { ScanEventRead, ScanEventType } from "@/lib/types";
import { cn } from "@/lib/utils/cn";

const EVENT_META: Record<
  ScanEventType,
  { icon: LucideIcon; tone: "neutral" | "info" | "ok" | "warn" | "error" }
> = {
  phase_started: { icon: Radar, tone: "info" },
  phase_completed: { icon: Sparkles, tone: "ok" },
  bright_data_call: { icon: Radar, tone: "info" },
  bright_data_call_replayed: { icon: Radar, tone: "neutral" },
  aiml_call: { icon: Brain, tone: "info" },
  aiml_call_replayed: { icon: Brain, tone: "neutral" },
  memory_write: { icon: Database, tone: "info" },
  memory_write_replayed: { icon: Database, tone: "neutral" },
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
} as const;

type ScanEventListProps = {
  events: ScanEventRead[];
  isLoading: boolean;
};

export function ScanEventList({ events, isLoading }: ScanEventListProps) {
  if (isLoading && events.length === 0) {
    return (
      <p className="text-[12px] text-[color:var(--color-fg-muted)]">Loading events…</p>
    );
  }

  if (events.length === 0) {
    return (
      <p className="text-[12px] text-[color:var(--color-fg-muted)]">No events yet.</p>
    );
  }

  return (
    <ScrollArea className="max-h-[260px]">
      <ol className="flex flex-col">
        {events.map((event) => {
          const meta = EVENT_META[event.event_type] ?? EVENT_META.info;
          const Icon = meta.icon;
          const replayed = event.event_type.endsWith("_replayed");
          return (
            <li
              key={event.id}
              className={cn(
                "flex items-start gap-2 border-b border-[color:var(--color-border-default)] py-1.5 text-[12px] leading-snug last:border-b-0",
              )}
            >
              <Icon className={cn("mt-0.5 size-3.5 shrink-0", TONE_CLASS[meta.tone])} aria-hidden />
              <div className="flex min-w-0 flex-1 flex-col">
                <span className="text-[color:var(--color-fg-primary)]">{event.message}</span>
                <span className="text-[10px] tracking-[0.04em] uppercase text-[color:var(--color-fg-muted)]">
                  #{event.sequence}
                  {event.phase ? ` · ${event.phase}` : null}
                  {replayed ? " · replayed" : null}
                </span>
              </div>
            </li>
          );
        })}
      </ol>
    </ScrollArea>
  );
}
