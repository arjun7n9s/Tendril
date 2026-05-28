import { cn } from "@/lib/utils/cn";

/**
 * Skeleton loader.
 *
 * Uses a left-to-right shimmer instead of an opacity pulse so loading
 * states feel directional ("data is on the way") rather than ambient.
 * The shimmer keyframe is defined in app/globals.css and is disabled
 * automatically when the user prefers reduced motion (the global rule
 * shortens animation durations to ~0).
 */
export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-[var(--radius-chip)] bg-[color:var(--color-raised)]",
        "before:absolute before:inset-0 before:translate-x-[-100%] before:bg-[linear-gradient(90deg,transparent,color-mix(in_oklab,var(--color-fg-primary)_5%,transparent),transparent)] before:animate-[tendril-shimmer_1.6s_ease-in-out_infinite]",
        className,
      )}
      {...props}
    />
  );
}
