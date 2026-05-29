"use client";

import { Eye, EyeOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAccountWatch, useUpsertWatch } from "@/lib/hooks/use-watchtower";
import { formatRelative } from "@/lib/utils/dates";

export function WatchToggle({ accountId }: { accountId: string }) {
  const watchQuery = useAccountWatch(accountId);
  const upsert = useUpsertWatch(accountId);

  const watch = watchQuery.data ?? null;
  const watching = Boolean(watch?.enabled);

  const toggle = () => {
    upsert.mutate({
      enabled: !watching,
      mode: watch?.mode ?? "mock",
      interval_seconds: watch?.interval_seconds,
    });
  };

  return (
    <Button
      variant={watching ? "secondary" : "ghost"}
      size="sm"
      className="h-7 gap-1.5 px-2 text-[12px]"
      loading={upsert.isPending}
      onClick={toggle}
      title={
        watching && watch?.next_due_at
          ? `Next auto-scan ${formatRelative(watch.next_due_at)}`
          : "Auto-scan this account on a schedule"
      }
    >
      {watching ? (
        <Eye className="size-3.5 text-signal" aria-hidden />
      ) : (
        <EyeOff className="size-3.5" aria-hidden />
      )}
      {watching ? "Watching" : "Watch"}
    </Button>
  );
}
