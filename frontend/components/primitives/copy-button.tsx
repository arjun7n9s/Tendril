"use client";

import { Check, Copy } from "lucide-react";
import { useEffect, useState } from "react";

import { cn } from "@/lib/utils/cn";

type CopyButtonProps = {
  value: string;
  label?: string;
  className?: string;
};

/**
 * Small inline button that copies the given string to the clipboard
 * and confirms the action by swapping its icon to a checkmark for
 * 1.5s. Used in the Evidence Drawer to copy the source URL without
 * forcing the user to open the original link first.
 */
export function CopyButton({ value, label = "Copy", className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const handle = setTimeout(() => setCopied(false), 1500);
    return () => clearTimeout(handle);
  }, [copied]);

  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(value);
          setCopied(true);
        } catch {
          /* clipboard API blocked, ignore */
        }
      }}
      aria-label={copied ? "Copied" : label}
      className={cn(
        "inline-flex h-6 items-center gap-1 rounded-[var(--radius-chip)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] px-1.5 text-[11px] font-medium text-[color:var(--color-fg-secondary)] transition-colors",
        "hover:bg-[color:var(--color-raised)] hover:text-[color:var(--color-fg-primary)]",
        copied &&
          "border-[color:color-mix(in_oklab,var(--color-signal)_30%,transparent)] bg-[color:var(--color-signal-soft)] text-[color:var(--color-signal)]",
        className,
      )}
    >
      {copied ? (
        <Check className="size-3" aria-hidden />
      ) : (
        <Copy className="size-3" aria-hidden />
      )}
      <span>{copied ? "Copied" : label}</span>
    </button>
  );
}
