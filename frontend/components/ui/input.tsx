import * as React from "react";

import { cn } from "@/lib/utils/cn";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, type, ...props }, ref) {
    return (
      <input
        ref={ref}
        type={type}
        className={cn(
          "flex h-9 w-full rounded-[var(--radius-input)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] px-3 py-1 text-[13px] text-[color:var(--color-fg-primary)] placeholder:text-[color:var(--color-fg-muted)] outline-none transition-colors",
          "focus:border-[color:var(--color-fg-primary)] focus:shadow-[0_0_0_3px_color-mix(in_oklab,var(--color-signal)_15%,transparent)]",
          "disabled:cursor-not-allowed disabled:opacity-60",
          className,
        )}
        {...props}
      />
    );
  },
);
