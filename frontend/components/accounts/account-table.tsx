"use client";

import { ArrowUpRight } from "lucide-react";
import Link from "next/link";

import { MonogramTile } from "@/components/primitives/monogram-tile";
import { StatusChip } from "@/components/primitives/status-chip";
import { Skeleton } from "@/components/ui/skeleton";
import type { AccountRead } from "@/lib/types";
import { cn } from "@/lib/utils/cn";
import { formatRelative } from "@/lib/utils/dates";

type AccountTableProps = {
  rows: AccountRead[];
  isLoading: boolean;
};

export function AccountTable({ rows, isLoading }: AccountTableProps) {
  if (isLoading) {
    return (
      <div className="overflow-hidden rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)]">
        <div className="grid grid-cols-[1.4fr_0.8fr_0.8fr_0.6fr_0.6fr_60px] gap-4 border-b border-[color:var(--color-border-default)] px-4 py-2 text-[11px] tracking-[0.04em] text-[color:var(--color-fg-muted)] uppercase">
          <span>Account</span>
          <span>Industry</span>
          <span>Region</span>
          <span>Size</span>
          <span>Updated</span>
          <span aria-hidden />
        </div>
        {Array.from({ length: 5 }).map((_, idx) => (
          <Skeleton key={idx} className="m-2 h-9 rounded-[6px]" />
        ))}
      </div>
    );
  }

  if (rows.length === 0) return null;

  return (
    <>
      <div className="flex flex-col overflow-hidden rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] shadow-[var(--shadow-flat)] md:hidden">
        {rows.map((account) => (
          <Link
            key={account.id}
            href={`/accounts/${account.id}`}
            className="flex items-start justify-between gap-3 border-b border-[color:var(--color-border-default)] px-3 py-3 last:border-b-0 hover:bg-[color:var(--color-canvas)]"
          >
            <div className="flex min-w-0 items-start gap-3">
              <MonogramTile name={account.name} seed={account.id} size="md" />
              <span className="flex min-w-0 flex-col">
                <span className="truncate text-[14px] font-medium text-[color:var(--color-fg-primary)]">
                  {account.name}
                </span>
                {account.domain ? (
                  <span className="truncate text-[12px] text-[color:var(--color-fg-muted)]">
                    {account.domain}
                  </span>
                ) : null}
                <span className="mt-1 text-[12px] text-[color:var(--color-fg-secondary)]">
                  {[account.industry, account.company_size].filter(Boolean).join(" · ") ||
                    "No firmographic data"}
                </span>
              </span>
            </div>
            <span className="flex shrink-0 flex-col items-end gap-1 text-right">
              <StatusChip kind="account" value={account.status} />
              <span className="text-[11px] text-[color:var(--color-fg-muted)] tabular-nums">
                {formatRelative(account.updated_at)}
              </span>
            </span>
          </Link>
        ))}
      </div>

      <div className="hidden overflow-hidden rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] shadow-[var(--shadow-flat)] md:block">
        <table className="w-full table-fixed border-collapse text-[13px]">
          <thead>
            <tr className="border-b border-[color:var(--color-border-default)] bg-[color:var(--color-canvas)] text-left text-[11px] tracking-[0.04em] text-[color:var(--color-fg-muted)] uppercase">
              <th scope="col" className="w-[34%] px-4 py-2 font-medium">
                Account
              </th>
              <th scope="col" className="w-[18%] px-3 py-2 font-medium">
                Industry
              </th>
              <th scope="col" className="hidden w-[14%] px-3 py-2 font-medium xl:table-cell">
                Region
              </th>
              <th scope="col" className="w-[10%] px-3 py-2 font-medium">
                Size
              </th>
              <th scope="col" className="w-[12%] px-3 py-2 font-medium">
                Status
              </th>
              <th scope="col" className="w-[12%] px-3 py-2 font-medium whitespace-nowrap">
                Updated
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((account, idx) => (
              <tr
                key={account.id}
                className={cn(
                  "group cursor-pointer border-b border-border/30 last:border-b-0 transition-all duration-200 ease-out",
                  "hover:bg-surface/85 hover:shadow-flat hover:scale-[1.001]",
                  idx % 2 === 1 ? "bg-surface/40" : "bg-transparent",
                )}
              >
                <td className="px-4 py-2.5">
                  <Link
                    href={`/accounts/${account.id}`}
                    className="inline-flex items-center gap-2.5 text-fg-primary"
                  >
                    <MonogramTile name={account.name} seed={account.id} size="md" />
                    <span className="flex flex-col">
                      <span className="font-medium">{account.name}</span>
                      {account.domain ? (
                        <span className="text-[11.5px] text-fg-muted">
                          {account.domain}
                        </span>
                      ) : null}
                    </span>
                    <ArrowUpRight
                      className="ml-1.5 size-3.5 text-fg-muted opacity-0 -translate-x-0.5 translate-y-0.5 transition-all duration-300 ease-out group-hover:opacity-100 group-hover:translate-x-0 group-hover:translate-y-0"
                      aria-hidden
                    />
                  </Link>
                </td>
                <td className="px-3 py-2.5 text-[color:var(--color-fg-secondary)]">
                  {account.industry ?? "—"}
                </td>
                <td className="hidden px-3 py-2.5 text-[color:var(--color-fg-secondary)] xl:table-cell">
                  {account.region ?? "—"}
                </td>
                <td className="px-3 py-2.5 text-[color:var(--color-fg-secondary)]">
                  {account.company_size ?? "—"}
                </td>
                <td className="px-3 py-2.5 whitespace-nowrap">
                  <StatusChip kind="account" value={account.status} />
                </td>
                <td className="px-3 py-2.5 whitespace-nowrap text-[color:var(--color-fg-muted)] tabular-nums">
                  {formatRelative(account.updated_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
