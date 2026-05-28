"use client";

import { motion, useReducedMotion } from "framer-motion";

type ScoreBarProps = {
  label: string;
  value: number;
  max: number;
  variant?: "signal" | "cobalt" | "evidence" | "graph";
};

const GRADIENT_MAP = {
  signal: "linear-gradient(90deg, #34d399 0%, #0c7c56 100%)",
  cobalt: "linear-gradient(90deg, #60a5fa 0%, #3457d5 100%)",
  evidence: "linear-gradient(90deg, #fbbf24 0%, #995f17 100%)",
  graph: "linear-gradient(90deg, #2dd4bf 0%, #107575 100%)",
} as const;

export function ScoreBar({ label, value, max, variant = "signal" }: ScoreBarProps) {
  const reduce = useReducedMotion();
  const safeValue = Math.max(0, Math.min(max, value));
  const pct = max === 0 ? 0 : (safeValue / max) * 100;

  return (
    <div className="flex flex-col gap-1.5 group/bar cursor-default transition-all duration-200 hover:scale-[1.01]">
      <div className="flex items-baseline justify-between gap-2 text-[10.5px] tracking-[0.03em] uppercase">
        <span className="text-fg-secondary font-medium transition-colors group-hover/bar:text-fg-primary">{label}</span>
        <span className="font-semibold tabular-nums text-fg-primary">
          {safeValue}
          <span className="text-fg-muted font-normal">/{max}</span>
        </span>
      </div>
      <div
        className="h-2 w-full overflow-hidden rounded-full bg-raised border border-border/40 transition-all duration-200 group-hover/bar:border-border/80 group-hover/bar:shadow-flat"
      >
        <motion.div
          initial={reduce ? false : { width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.75, ease: [0.22, 1, 0.36, 1] }}
          className="h-full rounded-full"
          style={{ backgroundImage: GRADIENT_MAP[variant] }}
        />
      </div>
    </div>
  );
}
