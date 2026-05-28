"use client";

import { Activity, LayoutGrid, Megaphone, Menu, Radar, Settings, Upload } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { cn } from "@/lib/utils/cn";

const NAV = [
  { href: "/accounts", label: "Accounts", icon: LayoutGrid },
  { href: "/outreach", label: "Outreach", icon: Megaphone },
  { href: "/imports", label: "Imports", icon: Upload },
  { href: "/signals", label: "Signal feed", icon: Activity },
  { href: "/scans", label: "Live scans", icon: Radar },
  { href: "/settings", label: "Settings", icon: Settings, disabled: true },
];

export function MobileNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      <header className="md:hidden sticky top-0 z-30 flex h-12 items-center justify-between border-b border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] px-3">
        <Link
          href="/accounts"
          className="inline-flex items-center gap-2 text-[15px] font-semibold tracking-[-0.01em] text-[color:var(--color-fg-primary)]"
        >
          <Glyph />
          Tendril
        </Link>
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="inline-flex size-9 items-center justify-center rounded-[var(--radius-button)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] text-[color:var(--color-fg-secondary)] hover:bg-[color:var(--color-raised)]"
          aria-label="Open navigation"
        >
          <Menu className="size-4" aria-hidden />
        </button>
      </header>
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent side="left" className="w-[260px] sm:max-w-[260px]">
          <SheetHeader>
            <SheetTitle>Navigate</SheetTitle>
          </SheetHeader>
          <ul className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-2">
            {NAV.map((item) => {
              const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`);
              const Icon = item.icon;
              if (item.disabled) {
                return (
                  <li key={item.href}>
                    <span className="flex items-center justify-between rounded-[var(--radius-button)] px-2.5 py-2 text-[13px] text-[color:var(--color-fg-muted)]">
                      <span className="inline-flex items-center gap-2">
                        <Icon className="size-4" aria-hidden />
                        {item.label}
                      </span>
                      <span className="text-[10px] tracking-[0.04em] uppercase">Soon</span>
                    </span>
                  </li>
                );
              }
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className={cn(
                      "flex items-center gap-2 rounded-[var(--radius-button)] px-2.5 py-2 text-[13px] font-medium transition-colors",
                      isActive
                        ? "bg-[color:var(--color-raised)] text-[color:var(--color-fg-primary)]"
                        : "text-[color:var(--color-fg-secondary)] hover:bg-[color:var(--color-raised)] hover:text-[color:var(--color-fg-primary)]",
                    )}
                  >
                    <Icon className="size-4" aria-hidden />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </SheetContent>
      </Sheet>
    </>
  );
}

function Glyph() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 32 32"
      fill="none"
      stroke="currentColor"
      strokeWidth={2.4}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M9 22 C 9 14, 14 10, 20 10 S 26 14, 24 19 C 22.4 23, 17 23, 16 19 C 15.2 15.6, 18.5 14, 20 16" />
      <circle cx="20" cy="16" r="1.6" fill="currentColor" stroke="none" />
    </svg>
  );
}
