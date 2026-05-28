import { MobileNav } from "./mobile-nav";
import { Sidebar } from "./sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-[color:var(--color-canvas)]">
      {/* Skip link: only visible when focused, lets keyboard users
          bypass the sidebar and mobile nav and jump straight into the
          main content. Lands the focus on the <main> element below. */}
      <a
        href="#tendril-main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-[var(--radius-button)] focus:bg-[color:var(--color-fg-primary)] focus:px-3 focus:py-2 focus:text-[12px] focus:font-medium focus:text-[color:var(--color-surface)] focus:shadow-[var(--shadow-overlay)]"
      >
        Skip to main content
      </a>
      <Sidebar />
      <div className="flex h-full min-w-0 flex-1 flex-col">
        <MobileNav />
        <main
          id="tendril-main"
          tabIndex={-1}
          className="relative flex-1 overflow-y-auto focus:outline-none"
        >
          {children}
        </main>
      </div>
    </div>
  );
}
