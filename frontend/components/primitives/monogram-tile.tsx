import { cn } from "@/lib/utils/cn";
import { initialsFor } from "@/lib/utils/initials";

type MonogramTileProps = {
  name: string;
  seed?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
  shape?: "rounded" | "circle";
};

const SIZE_CLASS = {
  sm: "size-6 text-[10px]",
  md: "size-8 text-[11.5px]",
  lg: "size-10 text-[13px]",
} as const;

function hashString(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 31 + value.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

const GRADIENTS = [
  {
    bg: "linear-gradient(135deg, rgba(12, 124, 86, 0.08) 0%, rgba(12, 124, 86, 0.02) 100%)",
    color: "var(--color-signal)",
    border: "1px solid rgba(12, 124, 86, 0.2)",
  },
  {
    bg: "linear-gradient(135deg, rgba(52, 87, 213, 0.08) 0%, rgba(52, 87, 213, 0.02) 100%)",
    color: "var(--color-cobalt)",
    border: "1px solid rgba(52, 87, 213, 0.2)",
  },
  {
    bg: "linear-gradient(135deg, rgba(153, 95, 23, 0.08) 0%, rgba(153, 95, 23, 0.02) 100%)",
    color: "var(--color-evidence)",
    border: "1px solid rgba(153, 95, 23, 0.2)",
  },
  {
    bg: "linear-gradient(135deg, rgba(16, 117, 117, 0.08) 0%, rgba(16, 117, 117, 0.02) 100%)",
    color: "var(--color-graph)",
    border: "1px solid rgba(16, 117, 117, 0.2)",
  },
  {
    bg: "linear-gradient(135deg, rgba(23, 26, 28, 0.06) 0%, rgba(23, 26, 28, 0.01) 100%)",
    color: "var(--color-fg-primary)",
    border: "1px solid rgba(23, 26, 28, 0.15)",
  },
];

export function MonogramTile({
  name,
  seed,
  size = "md",
  className,
  shape = "rounded",
}: MonogramTileProps) {
  const initials = initialsFor(name);
  const hash = hashString(seed ?? name);
  const style = GRADIENTS[hash % GRADIENTS.length]!;

  return (
    <span
      aria-hidden
      className={cn(
        "inline-flex items-center justify-center font-semibold transition-all duration-300",
        shape === "rounded" ? "rounded-[6px]" : "rounded-full",
        SIZE_CLASS[size],
        className,
      )}
      style={{
        background: style.bg,
        color: style.color,
        border: style.border,
      }}
    >
      {initials}
    </span>
  );
}
