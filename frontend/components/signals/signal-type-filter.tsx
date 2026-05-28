"use client";

import { SIGNAL_TYPES, type SignalType } from "@/lib/types";
import { cn } from "@/lib/utils/cn";

const LABEL: Record<SignalType, string> = {
  hiring: "Hiring",
  tech_stack: "Tech",
  migration: "Migration",
  funding: "Funding",
  product_launch: "Launch",
  leadership_change: "Leadership",
  competitor_mention: "Competitor",
  champion_move: "Champion",
  market_event: "Market",
  other: "Other",
};

type SignalTypeFilterProps = {
  value: SignalType | null;
  onChange: (value: SignalType | null) => void;
};

export function SignalTypeFilter({ value, onChange }: SignalTypeFilterProps) {
  return (
    <div className="flex flex-wrap items-center gap-1">
      {SIGNAL_TYPES.map((type) => {
        const active = value === type;
        return (
          <button
            key={type}
            type="button"
            onClick={() => onChange(active ? null : type)}
            className={cn(
              "inline-flex h-7 items-center rounded-[var(--radius-button)] border px-2 text-[12px] transition-colors",
              active
                ? "border-[color:var(--color-fg-primary)] bg-[color:var(--color-fg-primary)] text-[color:var(--color-surface)]"
                : "border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] text-[color:var(--color-fg-secondary)] hover:bg-[color:var(--color-raised)]",
            )}
          >
            {LABEL[type]}
          </button>
        );
      })}
    </div>
  );
}
