"use client";

import { FlaskConical, Radio } from "lucide-react";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useHealth } from "@/lib/hooks/use-health";
import { cn } from "@/lib/utils/cn";

export function ModeChip() {
  const { data } = useHealth();
  const mockMode = data?.mock_mode ?? true;

  return (
    <TooltipProvider delayDuration={150}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className={cn(
              "inline-flex items-center gap-1.5 rounded-[var(--radius-chip)] border px-2 py-0.5 text-[11px] font-medium tracking-[0.04em] uppercase",
              mockMode
                ? "border-border bg-raised text-fg-secondary"
                : "border-cobalt/25 bg-cobalt-soft text-cobalt",
            )}
          >
            {mockMode ? (
              <FlaskConical className="size-3" aria-hidden />
            ) : (
              <Radio className="size-3 animate-pulse" aria-hidden />
            )}
            {mockMode ? "Mock" : "Live"}
          </span>
        </TooltipTrigger>
        <TooltipContent>
          {mockMode
            ? "Mock mode is active. Scans run against bundled fixtures, no network calls to Bright Data."
            : "Live mode is active. Scans use Bright Data with cached fallback for missing sources."}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
