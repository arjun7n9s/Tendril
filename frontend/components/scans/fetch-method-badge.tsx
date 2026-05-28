import { Badge, type BadgeProps } from "@/components/ui/badge";
import type { FetchMethod } from "@/lib/types";

const LABEL: Record<FetchMethod, string> = {
  brightdata_mcp: "MCP",
  serp_api: "SERP",
  unlocker: "Unlocker",
  browser_api: "Browser",
  web_scraper_api: "Scraper",
  mock: "Mock",
  cached: "Cached",
};

const VARIANT: Record<FetchMethod, BadgeProps["variant"]> = {
  brightdata_mcp: "graph",
  serp_api: "cobalt",
  unlocker: "cobalt",
  browser_api: "cobalt",
  web_scraper_api: "cobalt",
  mock: "neutral",
  cached: "evidence",
};

export function FetchMethodBadge({ method }: { method: FetchMethod }) {
  return (
    <Badge variant={VARIANT[method]} size="sm">
      {LABEL[method]}
    </Badge>
  );
}
