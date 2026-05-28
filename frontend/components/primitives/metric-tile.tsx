import { cn } from "@/lib/utils/cn";

type MetricTileProps = {
  label: string;
  value: string | number;
  hint?: string;
  trend?: {
    direction: "up" | "down" | "flat";
    value: string;
  };
  className?: string;
};

export function MetricTile({ label, value, hint, trend, className }: MetricTileProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-1 rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] p-3 shadow-[var(--shadow-flat)]",
        className,
      )}
    >
      <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
        {label}
      </span>
      <div className="flex items-baseline gap-1.5">
        <span className="text-[22px] leading-none font-semibold tabular-nums text-[color:var(--color-fg-primary)]">
          {value}
        </span>
        {trend ? (
          <span
            className={cn(
              "text-[11px] font-medium",
              trend.direction === "up" && "text-[color:var(--color-signal)]",
              trend.direction === "down" && "text-[color:var(--color-risk)]",
              trend.direction === "flat" && "text-[color:var(--color-fg-muted)]",
            )}
          >
            {trend.direction === "up" ? "▲" : trend.direction === "down" ? "▼" : "—"} {trend.value}
          </span>
        ) : null}
      </div>
      {hint ? (
        <span className="text-[11px] text-[color:var(--color-fg-muted)]">{hint}</span>
      ) : null}
    </div>
  );
}
