import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils/cn";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-[var(--radius-chip)] border px-1.5 py-0.5 text-[11px] font-medium tracking-[0.01em] uppercase",
  {
    variants: {
      variant: {
        neutral:
          "border-[color:var(--color-border-default)] bg-[color:var(--color-raised)] text-[color:var(--color-fg-secondary)]",
        signal:
          "border-[color:color-mix(in_oklab,var(--color-signal)_30%,transparent)] bg-[color:var(--color-signal-soft)] text-[color:var(--color-signal)]",
        cobalt:
          "border-[color:color-mix(in_oklab,var(--color-cobalt)_25%,transparent)] bg-[color:var(--color-cobalt-soft)] text-[color:var(--color-cobalt)]",
        evidence:
          "border-[color:color-mix(in_oklab,var(--color-evidence)_30%,transparent)] bg-[color:var(--color-evidence-soft)] text-[color:var(--color-evidence)]",
        risk:
          "border-[color:color-mix(in_oklab,var(--color-risk)_30%,transparent)] bg-[color:var(--color-risk-soft)] text-[color:var(--color-risk)]",
        graph:
          "border-[color:color-mix(in_oklab,var(--color-graph)_25%,transparent)] bg-[color:var(--color-graph-soft)] text-[color:var(--color-graph)]",
        outline:
          "border-[color:var(--color-border-default)] bg-transparent text-[color:var(--color-fg-secondary)]",
      },
      size: {
        sm: "px-1.5 py-0.5 text-[10px]",
        md: "px-1.5 py-0.5 text-[11px]",
        lg: "px-2 py-1 text-[12px] normal-case tracking-normal",
      },
    },
    defaultVariants: {
      variant: "neutral",
      size: "md",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, size, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, size }), className)} {...props} />;
}

export { badgeVariants };
