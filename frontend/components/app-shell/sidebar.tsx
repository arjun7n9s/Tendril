"use client";

import { useSyncExternalStore } from "react";
import { useTheme } from "next-themes";
import {
  Activity,
  CircleAlert,
  LayoutGrid,
  Megaphone,
  Radar,
  Settings,
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
        "hidden md:flex h-full shrink-0 flex-col border-r border-border/40 bg-surface/65 backdrop-blur-md",
        "w-[212px]",
      )}
    >
      <Link
        href="/accounts"
        className="flex h-12 items-center gap-2 px-4 text-[15px] font-semibold tracking-[-0.015em] text-fg-primary hover:opacity-90 transition-opacity"
      >
        <span aria-hidden className="text-cobalt">
          <TendrilGlyph />
        </span>
        <span className="bg-gradient-to-r from-fg-primary to-fg-secondary bg-clip-text text-transparent">Tendril</span>
      </Link>
      <div className="border-t border-border/30" />
      <ul className="flex flex-1 flex-col gap-1.5 overflow-y-auto p-2">
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
                  "flex items-center gap-2.5 rounded-[var(--radius-button)] px-2.5 py-1.5 text-[13px] font-medium transition-all duration-200 ease-out border",
                  "hover:scale-[1.02] active:scale-[0.98]",
                  isActive
                    ? "bg-surface/80 border-border/60 text-fg-primary shadow-flat shadow-glow-cobalt/10"
                    : "text-fg-secondary border-transparent hover:bg-raised/70 hover:text-fg-primary",
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon className={cn("size-4 transition-transform duration-200", isActive ? "text-cobalt scale-110" : "text-fg-secondary")} aria-hidden />
                {item.label}
                {isActive && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[2.5px] h-[16px] rounded-r-full bg-cobalt shadow-[0_0_8px_rgba(52,87,213,0.6)]" />
                )}
              </Link>
            </li>
          );
        })}
      </ul>
      
      <div className="mx-3 mb-1.5 flex items-center justify-between rounded-[var(--radius-button)] border border-border/40 bg-surface/30 p-1 backdrop-blur-sm">
        <span className="pl-2 text-[10.5px] font-medium tracking-[0.02em] text-fg-secondary">Theme</span>
        <div className="flex items-center gap-0.5">
          <button
            onClick={() => setTheme("light")}
            className={cn(
              "p-1.5 rounded-[var(--radius-button)] transition-all duration-200 cursor-pointer",
              mounted && theme === "light"
                ? "bg-surface text-cobalt shadow-flat"
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
              "p-1.5 rounded-[var(--radius-button)] transition-all duration-200 cursor-pointer",
              mounted && theme === "dark"
                ? "bg-surface text-cobalt shadow-flat"
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
              "p-1.5 rounded-[var(--radius-button)] transition-all duration-200 cursor-pointer",
              mounted && theme === "system"
                ? "bg-surface text-cobalt shadow-flat"
                : "text-fg-muted hover:text-fg-primary"
            )}
            title="System theme"
            aria-label="System theme"
          >
            <Laptop className="size-3.5" />
          </button>
        </div>
      </div>

      <div className="m-3 rounded-[var(--radius-card)] border border-border/50 bg-surface/40 p-3 text-[12px] leading-snug text-fg-muted backdrop-blur-sm shadow-flat">
        <div className="mb-1.5 inline-flex items-center gap-1.5 font-medium text-fg-secondary">
          <CircleAlert className="size-3.5 text-cobalt animate-pulse" aria-hidden />
          <span>Demo Engine Active</span>
        </div>
        <p className="text-[11px] leading-normal text-fg-secondary">
          Autonomous change tracking. Gated behind secure sandbox credentials.
        </p>
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
