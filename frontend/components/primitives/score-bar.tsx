"use client";

import { motion, useReducedMotion } from "framer-motion";

import { cn } from "@/lib/utils/cn";

type ScoreBarProps = {
  label: string;
  value: number;
  max: number;
  variant?: "signal" | "cobalt" | "evidence" | "graph";
};

const COLOR_MAP = {
  signal: "var(--color-signal)",
  cobalt: "var(--color-cobalt)",
  evidence: "var(--color-evidence)",
  graph: "var(--color-graph)",
} as const;

export function ScoreBar({ label, value, max, variant = "signal" }: ScoreBarProps) {
  const reduce = useReducedMotion();
  const safeValue = Math.max(0, Math.min(max, value));
  const pct = max === 0 ? 0 : (safeValue / max) * 100;

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-baseline justify-between gap-2 text-[11px] tracking-[0.02em] uppercase">
        <span className="text-[color:var(--color-fg-secondary)]">{label}</span>
        <span className="font-medium tabular-nums text-[color:var(--color-fg-primary)]">
          {safeValue}
          <span className="text-[color:var(--color-fg-muted)]">/{max}</span>
        </span>
      </div>
      <div
        className={cn("h-1.5 w-full overflow-hidden rounded-full bg-[color:var(--color-raised)]")}
      >
        <motion.div
          initial={reduce ? false : { width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="h-full rounded-full"
          style={{ backgroundColor: COLOR_MAP[variant] }}
        />
      </div>
    </div>
  );
}
