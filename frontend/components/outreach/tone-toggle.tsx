"use client";

import { OUTREACH_TONES, type OutreachTone } from "@/lib/types";
import { cn } from "@/lib/utils/cn";

const LABEL: Record<OutreachTone, string> = {
  warm: "Warm",
  technical: "Technical",
  executive: "Executive",
  concise: "Concise",
};

type ToneToggleProps = {
  value: OutreachTone;
  onChange: (tone: OutreachTone) => void;
  disabled?: boolean;
};

export function ToneToggle({ value, onChange, disabled }: ToneToggleProps) {
  return (
    <div
      role="radiogroup"
      aria-label="Tone"
      className="inline-flex items-center gap-0.5 rounded-[var(--radius-button)] border border-[color:var(--color-border-default)] bg-[color:var(--color-raised)] p-0.5"
    >
      {OUTREACH_TONES.map((tone) => {
        const active = value === tone;
        return (
          <button
            key={tone}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(tone)}
            disabled={disabled}
            className={cn(
              "h-7 rounded-[calc(var(--radius-button)-2px)] px-2.5 text-[12px] font-medium transition-colors",
              active
                ? "bg-[color:var(--color-surface)] text-[color:var(--color-fg-primary)] shadow-[var(--shadow-flat)]"
                : "text-[color:var(--color-fg-secondary)] hover:text-[color:var(--color-fg-primary)]",
            )}
          >
            {LABEL[tone]}
          </button>
        );
      })}
    </div>
  );
}
