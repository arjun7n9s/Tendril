import type { LucideIcon } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils/cn";

type EmptyStateProps = {
  /** Optional fallback icon when no illustration is provided. */
  icon?: LucideIcon;
  /**
   * Preferred over `icon`: a wider, abstract SVG illustration. We
   * tint it via the parent's text color so it picks up the active
   * accent token (signal, evidence, fg-secondary, …).
   */
  illustration?: React.ReactElement<{ className?: string }>;
  illustrationTone?: "neutral" | "signal" | "evidence" | "risk" | "cobalt" | "graph";
  title: string;
  body?: string;
  action?: React.ReactNode;
  className?: string;
};

const TONE_CLASS = {
  neutral: "text-[color:var(--color-fg-muted)]",
  signal: "text-[color:var(--color-signal)]",
  evidence: "text-[color:var(--color-evidence)]",
  risk: "text-[color:var(--color-risk)]",
  cobalt: "text-[color:var(--color-cobalt)]",
  graph: "text-[color:var(--color-graph)]",
} as const;

export function EmptyState({
  icon: Icon,
  illustration,
  illustrationTone = "neutral",
  title,
  body,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-[var(--radius-card)] border border-dashed border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] px-6 py-12 text-center",
        className,
      )}
    >
      {illustration ? (
        <span className={cn("inline-flex w-32", TONE_CLASS[illustrationTone])}>
          {React.cloneElement(illustration, {
            className: cn("h-auto w-full", illustration.props.className),
          })}
        </span>
      ) : Icon ? (
        <span className="grid size-10 place-items-center rounded-full bg-[color:var(--color-raised)] text-[color:var(--color-fg-secondary)]">
          <Icon className="size-5" aria-hidden />
        </span>
      ) : null}
      <div className="flex flex-col gap-1">
        <h3 className="text-[15px] font-semibold text-[color:var(--color-fg-primary)]">{title}</h3>
        {body ? (
          <p className="max-w-sm text-[13px] text-[color:var(--color-fg-secondary)]">{body}</p>
        ) : null}
      </div>
      {action ? <div className="pt-1">{action}</div> : null}
    </div>
  );
}
