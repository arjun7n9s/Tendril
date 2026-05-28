"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils/cn";

export const Sheet = DialogPrimitive.Root;
export const SheetTrigger = DialogPrimitive.Trigger;
export const SheetClose = DialogPrimitive.Close;
export const SheetPortal = DialogPrimitive.Portal;

const SheetOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(function SheetOverlay({ className, ...props }, ref) {
  return (
    <DialogPrimitive.Overlay
      ref={ref}
      className={cn(
        "fixed inset-0 z-50 bg-[color:color-mix(in_oklab,var(--color-fg-primary)_38%,transparent)] backdrop-blur-[3px]",
        "data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
        className,
      )}
      {...props}
    />
  );
});

type Side = "right" | "left" | "top" | "bottom";

const SIDE_CLASSES: Record<Side, string> = {
  right:
    "inset-y-0 right-0 h-full w-full max-w-[480px] border-l data-[state=open]:slide-in-from-right data-[state=closed]:slide-out-to-right",
  left:
    "inset-y-0 left-0 h-full w-full max-w-[420px] border-r data-[state=open]:slide-in-from-left data-[state=closed]:slide-out-to-left",
  top:
    "inset-x-0 top-0 w-full max-h-[80vh] border-b data-[state=open]:slide-in-from-top data-[state=closed]:slide-out-to-top",
  bottom:
    "inset-x-0 bottom-0 w-full max-h-[80vh] border-t data-[state=open]:slide-in-from-bottom data-[state=closed]:slide-out-to-bottom",
};

interface SheetContentProps extends React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content> {
  side?: Side;
  showClose?: boolean;
}

export const SheetContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  SheetContentProps
>(function SheetContent({ side = "right", showClose = true, className, children, ...props }, ref) {
  return (
    <SheetPortal>
      <SheetOverlay />
      <DialogPrimitive.Content
        ref={ref}
        className={cn(
          "fixed z-50 flex flex-col border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] shadow-[var(--shadow-overlay)] focus:outline-none",
          "data-[state=open]:animate-in data-[state=closed]:animate-out duration-200",
          SIDE_CLASSES[side],
          className,
        )}
        {...props}
      >
        {children}
        {showClose ? (
          <DialogPrimitive.Close
            className={cn(
              "absolute top-3 right-3 rounded-[var(--radius-button)] p-1 text-[color:var(--color-fg-secondary)] hover:bg-[color:var(--color-raised)]",
            )}
            aria-label="Close"
          >
            <X className="size-4" />
          </DialogPrimitive.Close>
        ) : null}
      </DialogPrimitive.Content>
    </SheetPortal>
  );
});

export function SheetHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "border-b border-[color:var(--color-border-default)] px-5 py-4",
        className,
      )}
      {...props}
    />
  );
}

export function SheetFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "border-t border-[color:var(--color-border-default)] px-5 py-3",
        className,
      )}
      {...props}
    />
  );
}

export const SheetTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(function SheetTitle({ className, ...props }, ref) {
  return (
    <DialogPrimitive.Title
      ref={ref}
      className={cn(
        "text-[15px] leading-tight font-semibold text-[color:var(--color-fg-primary)]",
        className,
      )}
      {...props}
    />
  );
});

export const SheetDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(function SheetDescription({ className, ...props }, ref) {
  return (
    <DialogPrimitive.Description
      ref={ref}
      className={cn("text-[13px] text-[color:var(--color-fg-secondary)]", className)}
      {...props}
    />
  );
});
