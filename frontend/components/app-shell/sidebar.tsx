"use client";

import {
  Activity,
  CircleAlert,
  LayoutGrid,
  Megaphone,
  Radar,
  Settings,
  Upload,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils/cn";

type NavItem = {
  href: string;
  label: string;
  icon: typeof Activity;
  /** When true the item is in our MVP and should always render. */
  mvp: boolean;
  description?: string;
  comingSoon?: boolean;
};

const NAV_ITEMS: NavItem[] = [
  { href: "/accounts", label: "Accounts", icon: LayoutGrid, mvp: true },
  { href: "/outreach", label: "Outreach", icon: Megaphone, mvp: true },
  { href: "/imports", label: "Imports", icon: Upload, mvp: true },
  { href: "/signals", label: "Signal feed", icon: Activity, mvp: true },
  { href: "/scans", label: "Live scans", icon: Radar, mvp: true },
  { href: "/settings", label: "Settings", icon: Settings, mvp: false, comingSoon: true },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Primary"
      // Collapses to an icon-only rail at narrow widths (md and below)
      // and expands back to the full label column from md onward.
      className={cn(
        "hidden md:flex h-full shrink-0 flex-col border-r border-[color:var(--color-border-default)] bg-[color:var(--color-surface)]",
        "w-[212px]",
      )}
    >
      <Link
        href="/accounts"
        className="flex h-12 items-center gap-2 px-4 text-[15px] font-semibold tracking-[-0.01em] text-[color:var(--color-fg-primary)] hover:opacity-90"
      >
        <span aria-hidden className="text-[color:var(--color-fg-primary)]">
          <TendrilGlyph />
        </span>
        Tendril
      </Link>
      <div className="border-t border-[color:var(--color-border-default)]" />
      <ul className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-2">
        {NAV_ITEMS.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname?.startsWith(`${item.href}/`));
          const Icon = item.icon;
          if (item.comingSoon) {
            return (
              <li key={item.href}>
                <span
                  className={cn(
                    "flex items-center justify-between gap-2 rounded-[var(--radius-button)] px-2.5 py-1.5 text-[13px] text-[color:var(--color-fg-muted)]",
                  )}
                >
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
                className={cn(
                  "flex items-center gap-2 rounded-[var(--radius-button)] px-2.5 py-1.5 text-[13px] font-medium transition-colors",
                  isActive
                    ? "bg-[color:var(--color-raised)] text-[color:var(--color-fg-primary)]"
                    : "text-[color:var(--color-fg-secondary)] hover:bg-[color:var(--color-raised)] hover:text-[color:var(--color-fg-primary)]",
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon className="size-4" aria-hidden />
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
      <div className="m-2 rounded-[var(--radius-card)] border border-dashed border-[color:var(--color-border-default)] p-3 text-[12px] leading-snug text-[color:var(--color-fg-muted)]">
        <div className="mb-1 inline-flex items-center gap-1.5 text-[color:var(--color-fg-secondary)]">
          <CircleAlert className="size-3.5" aria-hidden />
          <span>Demo build</span>
        </div>
        Live web access requires Bright Data credentials. Mock mode runs offline.
      </div>
    </nav>
  );
}

/**
 * Mobile-only top nav strip is exported separately as
 * `components/app-shell/mobile-nav.tsx`. It renders below the `md`
 * breakpoint where this Sidebar is hidden.
 */

function TendrilGlyph() {
  return (
    <svg
      width="22"
      height="22"
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
