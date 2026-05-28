"use client";

import { MetricTile } from "@/components/primitives/metric-tile";
import { Skeleton } from "@/components/ui/skeleton";
import { useAccountsList } from "@/lib/hooks/use-accounts";

/**
 * Lightweight KPI strip for /accounts.
 *
 * For the hackathon we derive the metrics from the same paginated
 * /accounts list the table is using, plus a couple of focused queries
 * (sales-ready and near-miss). This avoids a dedicated /metrics
 * endpoint and keeps the strip honest: every number on screen is
 * directly traceable to a backend filter.
 */
export function AccountKpiStrip() {
  const { data: all, isLoading } = useAccountsList({ limit: 1 });
  const { data: salesReady } = useAccountsList({ sales_ready: true, limit: 1 });
  const { data: nearMiss } = useAccountsList({ near_miss: true, limit: 1 });
  const { data: targets } = useAccountsList({ status: "target", limit: 1 });

  const tiles = [
    { label: "Accounts", value: all?.total ?? 0, hint: "in scope" },
    { label: "Sales-ready", value: salesReady?.total ?? 0, hint: "score ≥ 70" },
    { label: "Needs one more", value: nearMiss?.total ?? 0, hint: "score 55–69" },
    { label: "Targets", value: targets?.total ?? 0, hint: "active targets" },
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
        {tiles.map((tile) => (
          <Skeleton key={tile.label} className="h-[78px] rounded-[var(--radius-card)]" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
      {tiles.map((tile) => (
        <MetricTile key={tile.label} label={tile.label} value={tile.value} hint={tile.hint} />
      ))}
    </div>
  );
}
