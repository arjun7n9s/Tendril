import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils/cn";

type EmptyStateProps = {
  icon?: LucideIcon;
  title: string;
  body?: string;
  action?: React.ReactNode;
  className?: string;
};

export function EmptyState({ icon: Icon, title, body, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-[var(--radius-card)] border border-dashed border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] px-6 py-12 text-center",
        className,
      )}
    >
      {Icon ? (
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
