"use client";

import { useMemo } from "react";

import { cn } from "@/lib/utils/cn";
import { formatTimecode } from "@/lib/utils/timecode";

type QuoteWaveformProps = {
  durationSeconds?: number | null;
  quoteStart?: number | null;
  quoteEnd?: number | null;
  /** Stable seed so the bar heights are deterministic per source. */
  seed?: string;
  className?: string;
};

/**
 * A lightweight, non-interactive waveform that visualizes where in a recording
 * a quote sits. It sells "we actually listened to this" without shipping an
 * audio engine. Bar heights are deterministic from a seed so the same source
 * always renders the same shape.
 */
export function QuoteWaveform({
  durationSeconds,
  quoteStart,
  quoteEnd,
  seed = "tendril",
  className,
}: QuoteWaveformProps) {
  const BAR_COUNT = 64;
  const duration = durationSeconds && durationSeconds > 0 ? durationSeconds : null;

  const bars = useMemo(() => {
    // Deterministic pseudo-random heights from the seed.
    let h = 2166136261;
    for (let i = 0; i < seed.length; i++) {
      h ^= seed.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    const out: number[] = [];
    for (let i = 0; i < BAR_COUNT; i++) {
      h ^= h << 13;
      h ^= h >>> 17;
      h ^= h << 5;
      const r = ((h >>> 0) % 1000) / 1000;
      // Bias toward mid heights with some variation.
      out.push(0.25 + r * 0.7);
    }
    return out;
  }, [seed]);

  const startFrac =
    duration && quoteStart != null ? Math.max(0, Math.min(1, quoteStart / duration)) : null;
  const endFrac =
    duration && quoteEnd != null ? Math.max(0, Math.min(1, quoteEnd / duration)) : null;

  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <div
        className="flex h-12 items-center gap-[2px]"
        role="img"
        aria-label={
          quoteStart != null
            ? `Quote located at ${formatTimecode(quoteStart)} in the recording`
            : "Audio waveform"
        }
      >
        {bars.map((height, i) => {
          const frac = i / BAR_COUNT;
          const inQuote =
            startFrac != null && endFrac != null
              ? frac >= startFrac && frac <= Math.max(endFrac, startFrac + 0.01)
              : false;
          return (
            <span
              key={i}
              className={cn(
                "w-full flex-1 rounded-full transition-colors",
                inQuote ? "bg-evidence" : "bg-border-strong/60",
              )}
              style={{ height: `${Math.round(height * 100)}%` }}
            />
          );
        })}
      </div>
      {duration ? (
        <div className="flex justify-between font-mono text-[10px] tabular-nums text-fg-muted">
          <span>0:00</span>
          {quoteStart != null ? (
            <span className="text-evidence">{formatTimecode(quoteStart)}</span>
          ) : null}
          <span>{formatTimecode(duration)}</span>
        </div>
      ) : null}
    </div>
  );
}
