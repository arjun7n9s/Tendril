import { cn } from "@/lib/utils/cn";
import { scoreTier, scoreTierAccent, type ScoreTier } from "@/lib/utils/score";
import type { ScoreRead } from "@/lib/types";

type ScoreRingProps = {
  score: Pick<ScoreRead, "total_score" | "sales_ready"> | null | undefined;
  size?: number;
  strokeWidth?: number;
  className?: string;
  showLabel?: boolean;
};

export function ScoreRing({
  score,
  size = 64,
  strokeWidth = 6,
  className,
  showLabel = true,
}: ScoreRingProps) {
  const tier: ScoreTier = scoreTier(score);
  const accent = scoreTierAccent(tier);
  const value = Math.max(0, Math.min(100, score?.total_score ?? 0));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (value / 100) * circumference;

  return (
    <div
      className={cn("relative inline-flex items-center justify-center", className)}
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-border-default)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          className={cn(accent.ring, "transition-[stroke-dashoffset] duration-500 ease-out")}
        />
      </svg>
      {showLabel ? (
        <div
          className="absolute inset-0 flex flex-col items-center justify-center leading-none"
          aria-label={`Total score ${value} out of 100`}
        >
          <span className="text-[15px] font-semibold tabular-nums text-[color:var(--color-fg-primary)]">
            {value}
          </span>
          <span className={cn("text-[9px] tracking-wider uppercase", accent.fg)}>/100</span>
        </div>
      ) : null}
    </div>
  );
}
