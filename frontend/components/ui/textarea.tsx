import * as React from "react";

import { cn } from "@/lib/utils/cn";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(function Textarea({ className, ...props }, ref) {
  return (
    <textarea
      ref={ref}
      className={cn(
        "flex min-h-[120px] w-full rounded-[var(--radius-input)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] px-3 py-2 text-[13px] leading-6 text-[color:var(--color-fg-primary)] placeholder:text-[color:var(--color-fg-muted)] outline-none transition-colors",
        "focus:border-[color:var(--color-fg-primary)] focus:shadow-[0_0_0_3px_color-mix(in_oklab,var(--color-signal)_15%,transparent)]",
        "disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      {...props}
    />
  );
});
