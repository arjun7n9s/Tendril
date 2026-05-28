import { cn } from "@/lib/utils/cn";
import { initialsFor, paletteFor } from "@/lib/utils/initials";

type MonogramTileProps = {
  name: string;
  seed?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
  shape?: "rounded" | "circle";
};

const SIZE_CLASS = {
  sm: "size-6 text-[10px]",
  md: "size-8 text-[12px]",
  lg: "size-10 text-[13px]",
} as const;

export function MonogramTile({
  name,
  seed,
  size = "md",
  className,
  shape = "rounded",
}: MonogramTileProps) {
  const palette = paletteFor(seed ?? name);
  const initials = initialsFor(name);

  return (
    <span
      aria-hidden
      className={cn(
        "inline-flex items-center justify-center font-semibold ring-1 ring-inset ring-black/5",
        shape === "rounded" ? "rounded-[6px]" : "rounded-full",
        SIZE_CLASS[size],
        palette.bg,
        palette.fg,
        className,
      )}
    >
      {initials}
    </span>
  );
}
