"use client";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useHealth } from "@/lib/hooks/use-health";
import type { HealthResponse, IntegrationFlag } from "@/lib/types";
import { cn } from "@/lib/utils/cn";

type IntegrationKey = keyof Pick<
  HealthResponse,
  "bright_data_rest" | "bright_data_browser" | "bright_data_mcp" | "aiml_api" | "cognee"
>;

const INTEGRATIONS: { key: IntegrationKey; label: string; description: string }[] = [
  { key: "bright_data_rest", label: "Bright Data", description: "SERP + Web Unlocker via REST" },
  {
    key: "bright_data_browser",
    label: "Browser API",
    description: "Bright Data Scraping Browser for JS-heavy pages",
  },
  { key: "bright_data_mcp", label: "MCP", description: "Bright Data MCP server (optional)" },
  { key: "aiml_api", label: "AI/ML API", description: "Extraction, briefing, draft models" },
  { key: "cognee", label: "Cognee", description: "Persistent graph memory" },
];

export function IntegrationStatus() {
  const { data, isLoading } = useHealth();

  return (
    <TooltipProvider delayDuration={150}>
      <ul className="flex items-center gap-1.5">
        {INTEGRATIONS.map(({ key, label, description }) => {
          const flag: IntegrationFlag = data?.[key] ?? "not_configured";
          const configured = flag === "configured";
          return (
            <li key={key}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-[var(--radius-chip)] border px-2 py-0.5 text-[11px] font-medium tracking-[0.01em] transition-all duration-300 ease-out",
                      configured
                        ? "border-signal/30 bg-signal-soft/70 text-signal shadow-flat shadow-glow-emerald/5 hover:border-signal/50"
                        : "border-border/60 bg-raised/60 text-fg-muted",
                    )}
                  >
                    {configured ? (
                      <span className="relative flex h-1.5 w-1.5 shrink-0" aria-hidden>
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-signal opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-signal"></span>
                      </span>
                    ) : (
                      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-fg-muted/40" aria-hidden />
                    )}
                    {label}
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="font-medium">
                    {label} · {configured ? "Configured" : "Not configured"}
                  </p>
                  <p className="opacity-80">{description}</p>
                </TooltipContent>
              </Tooltip>
            </li>
          );
        })}
        {isLoading ? (
          <li className="text-[11px] text-[color:var(--color-fg-muted)]">checking…</li>
        ) : null}
      </ul>
    </TooltipProvider>
  );
}
