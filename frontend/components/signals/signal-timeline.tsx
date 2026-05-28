"use client";

import { format, getISOWeek, getYear, parseISO } from "date-fns";
import { useMemo } from "react";

import { SignalCard } from "@/components/signals/signal-card";
import type { SignalRead } from "@/lib/types";

type Bucket = {
  key: string;
  label: string;
  signals: SignalRead[];
};

function bucketLabel(date: Date): string {
  const week = getISOWeek(date);
  const year = getYear(date);
  return `Week ${String(week).padStart(2, "0")} · ${year}`;
}

function safeParse(value: string | null | undefined): Date | null {
  if (!value) return null;
  try {
    const d = parseISO(value);
    return Number.isNaN(d.getTime()) ? null : d;
  } catch {
    return null;
  }
}

export function SignalTimeline({ signals }: { signals: SignalRead[] }) {
  const buckets = useMemo<Bucket[]>(() => {
    const map = new Map<string, Bucket>();
    for (const signal of signals) {
      const date = safeParse(signal.observed_at) ?? safeParse(signal.created_at);
      if (!date) continue;
      const key = `${getYear(date)}-W${String(getISOWeek(date)).padStart(2, "0")}`;
      const existing = map.get(key);
      if (existing) {
        existing.signals.push(signal);
      } else {
        map.set(key, { key, label: bucketLabel(date), signals: [signal] });
      }
    }
    return Array.from(map.values()).sort((a, b) => (a.key < b.key ? 1 : -1));
  }, [signals]);

  if (buckets.length === 0) {
    return (
      <p className="text-[13px] text-[color:var(--color-fg-muted)]">
        No timestamped signals yet.
      </p>
    );
  }

  return (
    <ol className="relative flex flex-col gap-6">
      {buckets.map((bucket, bucketIdx) => (
        <li key={bucket.key} className="flex flex-col gap-3">
          <header className="flex items-baseline justify-between gap-3">
            <h3 className="text-[12px] font-semibold tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
              {bucket.label}
            </h3>
            <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-muted)]">
              {bucket.signals.length} signal{bucket.signals.length === 1 ? "" : "s"}
            </span>
          </header>
          <div className="relative flex flex-col gap-3 pl-6">
            {/* vertical rail */}
            <span
              aria-hidden
              className="absolute top-0 bottom-0 left-[7px] w-px bg-[color:var(--color-border-default)]"
            />
            {bucket.signals.map((signal) => {
              const date = safeParse(signal.observed_at) ?? safeParse(signal.created_at);
              return (
                <div key={signal.id} className="relative">
                  {/* dot */}
                  <span
                    aria-hidden
                    className="absolute -left-[19px] top-4 grid size-3.5 place-items-center rounded-full bg-[color:var(--color-surface)] ring-2 ring-[color:var(--color-border-default)]"
                  >
                    <span className="size-1.5 rounded-full bg-[color:var(--color-cobalt)]" />
                  </span>
                  {date ? (
                    <p className="mb-1 text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-muted)]">
                      {format(date, "EEE, MMM d")}
                    </p>
                  ) : null}
                  <SignalCard signal={signal} />
                </div>
              );
            })}
          </div>
          {bucketIdx < buckets.length - 1 ? null : null}
        </li>
      ))}
    </ol>
  );
}
