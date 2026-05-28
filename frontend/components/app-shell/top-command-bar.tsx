"use client";

import { Search } from "lucide-react";

import { IntegrationStatus } from "./integration-status";
import { ModeChip } from "./mode-chip";

import { cn } from "@/lib/utils/cn";

type TopCommandBarProps = {
  title: string;
  subtitle?: string;
  primaryAction?: React.ReactNode;
  /** Optional: render a contextual filter or tab strip beneath the title row. */
  meta?: React.ReactNode;
};

export function TopCommandBar({ title, subtitle, primaryAction, meta }: TopCommandBarProps) {
  return (
    <header
      className={cn(
        "sticky top-0 z-30 flex flex-col gap-3 border-b border-[color:var(--color-border-default)] bg-[color:var(--color-surface)]/95 px-6 py-3 backdrop-blur-sm",
      )}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="flex flex-col gap-0.5">
          <h1 className="text-[18px] leading-tight font-semibold tracking-[-0.01em] text-[color:var(--color-fg-primary)]">
            {title}
          </h1>
          {subtitle ? (
            <p className="text-[12px] text-[color:var(--color-fg-secondary)]">{subtitle}</p>
          ) : null}
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            className={cn(
              "inline-flex h-8 items-center gap-2 rounded-[var(--radius-button)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] px-2.5 text-[12px] text-[color:var(--color-fg-muted)]",
              "hover:bg-[color:var(--color-raised)]",
            )}
            aria-label="Search accounts, signals, evidence (coming soon)"
            disabled
          >
            <Search className="size-3.5" aria-hidden />
            <span>Search…</span>
            <kbd className="hidden h-5 items-center rounded border border-[color:var(--color-border-default)] bg-[color:var(--color-canvas)] px-1 text-[10px] font-medium text-[color:var(--color-fg-muted)] sm:inline-flex">
              ⌘K
            </kbd>
          </button>
          <ModeChip />
          <IntegrationStatus />
          {primaryAction ? <div className="ml-2">{primaryAction}</div> : null}
        </div>
      </div>
      {meta ? <div>{meta}</div> : null}
    </header>
  );
}
