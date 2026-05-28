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
        "sticky top-0 z-30 flex flex-col gap-3 border-b border-border/40 bg-surface/70 px-6 py-3 backdrop-blur-md",
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-col gap-0.5">
          <h1 className="text-[17px] leading-tight font-semibold tracking-[-0.015em] text-fg-primary">
            {title}
          </h1>
          {subtitle ? (
            <p className="text-[11px] text-fg-muted">{subtitle}</p>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <button
            type="button"
            className={cn(
              "hidden md:inline-flex h-8 items-center gap-2 rounded-[var(--radius-button)] border border-border/50 bg-surface/50 px-2.5 text-[12px] text-fg-muted transition-all duration-200 ease-out",
              "hover:bg-raised/80 hover:border-border hover:scale-[1.01] active:scale-[0.99]",
            )}
            aria-label="Search (coming soon)"
            aria-disabled
            tabIndex={-1}
            disabled
          >
            <Search className="size-3.5" aria-hidden />
            <span>Search…</span>
            <kbd className="hidden h-5 items-center rounded border border-[color:var(--color-border-default)] bg-[color:var(--color-canvas)] px-1 text-[10px] font-medium text-[color:var(--color-fg-muted)] xl:inline-flex">
              ⌘K
            </kbd>
          </button>
          <ModeChip />
          <div className="hidden lg:flex">
            <IntegrationStatus />
          </div>
          {primaryAction ? <div className="ml-auto sm:ml-2">{primaryAction}</div> : null}
        </div>
      </div>
      {meta ? <div>{meta}</div> : null}
    </header>
  );
}
