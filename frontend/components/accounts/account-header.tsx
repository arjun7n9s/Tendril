"use client";

import { ExternalLink, Radar } from "lucide-react";

import { MonogramTile } from "@/components/primitives/monogram-tile";
import { StatusChip } from "@/components/primitives/status-chip";
import { Button } from "@/components/ui/button";
import { COPY } from "@/lib/copy";
import type { AccountRead } from "@/lib/types";
import { cn } from "@/lib/utils/cn";
import { formatRelative } from "@/lib/utils/dates";

type AccountHeaderProps = {
  account: AccountRead;
  lastScannedAt?: string | null;
  onRunScan?: () => void;
  isScanRunning?: boolean;
};

export function AccountHeader({
  account,
  lastScannedAt,
  onRunScan,
  isScanRunning,
}: AccountHeaderProps) {
  return (
    <header className="flex flex-col gap-3 border-b border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] px-6 py-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <MonogramTile name={account.name} seed={account.id} size="lg" />
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <h1 className="text-[20px] leading-tight font-semibold tracking-[-0.01em] text-[color:var(--color-fg-primary)]">
                {account.name}
              </h1>
              <StatusChip kind="account" value={account.status} />
            </div>
            <div className="flex flex-wrap items-center gap-3 text-[12px] text-[color:var(--color-fg-secondary)]">
              {account.domain ? (
                <a
                  href={`https://${account.domain.replace(/^https?:\/\//, "")}`}
                  className="inline-flex items-center gap-1 hover:text-[color:var(--color-fg-primary)]"
                  target="_blank"
                  rel="noreferrer"
                >
                  {account.domain}
                  <ExternalLink className="size-3" aria-hidden />
                </a>
              ) : null}
              {account.industry ? <span>{account.industry}</span> : null}
              {account.company_size ? <span>{account.company_size}</span> : null}
              {account.region ? <span>{account.region}</span> : null}
              <span>
                Last scanned{" "}
                <span className="text-[color:var(--color-fg-muted)]">
                  {formatRelative(lastScannedAt)}
                </span>
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={onRunScan}
            loading={isScanRunning}
            variant="signal"
            size="md"
            className={cn("font-semibold")}
          >
            {!isScanRunning ? <Radar className="size-3.5" aria-hidden /> : null}
            {isScanRunning ? COPY.scan.primaryRunning : COPY.scan.primary}
          </Button>
        </div>
      </div>
    </header>
  );
}
