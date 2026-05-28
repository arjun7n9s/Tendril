"use client";

import { CheckCircle2, CircleDashed } from "lucide-react";

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
                      "inline-flex items-center gap-1 rounded-[var(--radius-chip)] border px-1.5 py-0.5 text-[11px] font-medium tracking-[0.01em]",
                      configured
                        ? "border-[color:color-mix(in_oklab,var(--color-signal)_30%,transparent)] bg-[color:var(--color-signal-soft)] text-[color:var(--color-signal)]"
                        : "border-[color:var(--color-border-default)] bg-[color:var(--color-raised)] text-[color:var(--color-fg-muted)]",
                    )}
                  >
                    {configured ? (
                      <CheckCircle2 className="size-3" aria-hidden />
                    ) : (
                      <CircleDashed className="size-3" aria-hidden />
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
