"use client";

import { useSyncExternalStore } from "react";
import { useTheme } from "next-themes";
import {
  Activity,
  LayoutGrid,
  Megaphone,
  Radar,
  Settings,
  Sunrise,
  Upload,
  Sun,
  Moon,
  Laptop,
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
  { href: "/today", label: "Today", icon: Sunrise, mvp: true },
  { href: "/accounts", label: "Accounts", icon: LayoutGrid, mvp: true },
  { href: "/outreach", label: "Outreach", icon: Megaphone, mvp: true },
  { href: "/imports", label: "Imports", icon: Upload, mvp: true },
  { href: "/signals", label: "Signal feed", icon: Activity, mvp: true },
  { href: "/scans", label: "Live scans", icon: Radar, mvp: true },
  { href: "/settings", label: "Settings", icon: Settings, mvp: true },
];

export function Sidebar() {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  // Hydration guard for next-themes. The server cannot know the
  // resolved theme, so we treat it as unknown until the client has
  // mounted. useSyncExternalStore replaces the previous setState-in-
  // effect pattern that React 19's hooks rules disallow.
  const mounted = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );

  return (
    <nav
      aria-label="Primary"
      className={cn(
        "hidden md:flex h-full shrink-0 flex-col border-r border-border/30 bg-surface",
        "w-[212px]",
      )}
    >
      <Link
        href="/today"
        className="flex h-12 items-center gap-2 px-4 text-[15px] font-semibold tracking-[-0.015em] text-fg-primary hover:opacity-90 transition-opacity"
      >
        <span aria-hidden className="text-fg-primary">
          <TendrilGlyph />
        </span>
        <span className="bg-gradient-to-r from-fg-primary to-fg-secondary bg-clip-text text-transparent">Tendril</span>
      </Link>
      <div className="border-t border-border/20" />
      <ul className="flex flex-1 flex-col gap-1 overflow-y-auto p-2">
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
                    "flex items-center justify-between gap-2 rounded-[var(--radius-button)] px-2.5 py-1.5 text-[13px] text-fg-muted",
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
            <li key={item.href} className="relative">
              <Link
                href={item.href}
                className={cn(
                  "flex items-center gap-2.5 rounded-[var(--radius-button)] px-2.5 py-1.5 text-[13px] font-medium transition-colors duration-150 border",
                  isActive
                    ? "bg-raised border-border/60 text-fg-primary shadow-flat"
                    : "text-fg-secondary border-transparent hover:bg-raised/60 hover:text-fg-primary",
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon className={cn("size-4", isActive ? "text-fg-primary" : "text-fg-secondary")} aria-hidden />
                {item.label}
                {isActive && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[2px] h-[14px] rounded-r-full bg-fg-primary" />
                )}
              </Link>
            </li>
          );
        })}
      </ul>
      
      <div className="mx-3 mb-1.5 flex items-center justify-between rounded-[var(--radius-button)] border border-border/20 bg-raised/30 p-1">
        <span className="pl-2 text-[10.5px] font-medium tracking-[0.02em] text-fg-secondary">Theme</span>
        <div className="flex items-center gap-0.5">
          <button
            onClick={() => setTheme("light")}
            className={cn(
              "p-1.5 rounded-[var(--radius-button)] transition-colors duration-150 cursor-pointer border border-transparent",
              mounted && theme === "light"
                ? "bg-surface text-fg-primary shadow-flat border-border/40"
                : "text-fg-muted hover:text-fg-primary"
            )}
            title="Light theme"
            aria-label="Light theme"
          >
            <Sun className="size-3.5" />
          </button>
          <button
            onClick={() => setTheme("dark")}
            className={cn(
              "p-1.5 rounded-[var(--radius-button)] transition-colors duration-150 cursor-pointer border border-transparent",
              mounted && theme === "dark"
                ? "bg-surface text-fg-primary shadow-flat border-border/40"
                : "text-fg-muted hover:text-fg-primary"
            )}
            title="Dark theme"
            aria-label="Dark theme"
          >
            <Moon className="size-3.5" />
          </button>
          <button
            onClick={() => setTheme("system")}
            className={cn(
              "p-1.5 rounded-[var(--radius-button)] transition-colors duration-150 cursor-pointer border border-transparent",
              mounted && theme === "system"
                ? "bg-surface text-fg-primary shadow-flat border-border/40"
                : "text-fg-muted hover:text-fg-primary"
            )}
            title="System theme"
            aria-label="System theme"
          >
            <Laptop className="size-3.5" />
          </button>
        </div>
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
