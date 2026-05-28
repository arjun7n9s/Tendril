"use client";

import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils/cn";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[var(--radius-button)] font-medium transition-colors focus-visible:outline-2 disabled:pointer-events-none disabled:opacity-60 select-none",
  {
    variants: {
      variant: {
        primary:
          "bg-[color:var(--color-fg-primary)] text-[color:var(--color-surface)] hover:bg-[color:color-mix(in_oklab,var(--color-fg-primary)_92%,white)] active:bg-black",
        secondary:
          "bg-[color:var(--color-surface)] text-[color:var(--color-fg-primary)] border border-[color:var(--color-border-default)] hover:bg-[color:var(--color-raised)]",
        ghost:
          "bg-transparent text-[color:var(--color-fg-primary)] hover:bg-[color:var(--color-raised)]",
        signal:
          "bg-[color:var(--color-signal)] text-white hover:bg-[color:color-mix(in_oklab,var(--color-signal)_92%,black)]",
        destructive:
          "bg-[color:var(--color-risk)] text-white hover:bg-[color:color-mix(in_oklab,var(--color-risk)_92%,black)]",
        outline:
          "border border-[color:var(--color-border-default)] bg-transparent text-[color:var(--color-fg-primary)] hover:bg-[color:var(--color-raised)]",
        link:
          "h-auto p-0 text-[color:var(--color-fg-primary)] underline-offset-4 hover:underline",
      },
      size: {
        sm: "h-8 px-3 text-[13px]",
        md: "h-9 px-3.5 text-[13px]",
        lg: "h-10 px-4 text-sm",
        icon: "h-9 w-9 p-0",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant, size, asChild = false, loading = false, disabled, children, ...props },
  ref,
) {
  const Component = asChild ? Slot : "button";
  // When `asChild` is true, Slot requires a single child element. We
  // therefore can't inject a loading spinner alongside the consumer's
  // child. The loading flag still toggles `disabled` so the click is
  // suppressed, which is the more important behavior.
  if (asChild) {
    return (
      <Component
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        {...(loading || disabled ? { "aria-disabled": true } : null)}
        {...props}
      >
        {children}
      </Component>
    );
  }
  return (
    <Component
      ref={ref}
      className={cn(buttonVariants({ variant, size }), className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <Loader2 className="size-4 animate-spin" aria-hidden /> : null}
      {children}
    </Component>
  );
});

export { buttonVariants };
