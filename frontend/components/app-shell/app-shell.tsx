import { MobileNav } from "./mobile-nav";
import { Sidebar } from "./sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-[color:var(--color-canvas)]">
      <Sidebar />
      <div className="flex h-full min-w-0 flex-1 flex-col">
        <MobileNav />
        <main className="relative flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
