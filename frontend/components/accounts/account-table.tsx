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
        <div className="grid grid-cols-[1.4fr_0.8fr_0.8fr_0.6fr_0.6fr_60px] gap-4 border-b border-[color:var(--color-border-default)] px-4 py-2 text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-muted)]">
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
    <div className="overflow-hidden rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] shadow-[var(--shadow-flat)]">
      <table className="w-full table-fixed border-collapse text-[13px]">
        <thead>
          <tr className="border-b border-[color:var(--color-border-default)] bg-[color:var(--color-canvas)] text-left text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-muted)]">
            <th scope="col" className="w-[34%] px-4 py-2 font-medium">
              Account
            </th>
            <th scope="col" className="w-[18%] px-3 py-2 font-medium">
              Industry
            </th>
            <th scope="col" className="w-[14%] px-3 py-2 font-medium">
              Region
            </th>
            <th scope="col" className="w-[10%] px-3 py-2 font-medium">
              Size
            </th>
            <th scope="col" className="w-[12%] px-3 py-2 font-medium">
              Status
            </th>
            <th scope="col" className="w-[12%] px-3 py-2 font-medium">
              Updated
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((account, idx) => (
            <tr
              key={account.id}
              className={cn(
                "group cursor-pointer border-b border-[color:var(--color-border-default)] last:border-b-0 hover:bg-[color:var(--color-canvas)]",
                idx % 2 === 1 && "bg-[color:var(--color-surface)]",
              )}
            >
              <td className="px-4 py-2.5">
                <Link
                  href={`/accounts/${account.id}`}
                  className="inline-flex items-center gap-2.5 text-[color:var(--color-fg-primary)]"
                >
                  <MonogramTile name={account.name} seed={account.id} size="md" />
                  <span className="flex flex-col">
                    <span className="font-medium">{account.name}</span>
                    {account.domain ? (
                      <span className="text-[12px] text-[color:var(--color-fg-muted)]">
                        {account.domain}
                      </span>
                    ) : null}
                  </span>
                  <ArrowUpRight
                    className="ml-1 size-3.5 text-[color:var(--color-fg-muted)] opacity-0 transition-opacity group-hover:opacity-100"
                    aria-hidden
                  />
                </Link>
              </td>
              <td className="px-3 py-2.5 text-[color:var(--color-fg-secondary)]">
                {account.industry ?? "—"}
              </td>
              <td className="px-3 py-2.5 text-[color:var(--color-fg-secondary)]">
                {account.region ?? "—"}
              </td>
              <td className="px-3 py-2.5 text-[color:var(--color-fg-secondary)]">
                {account.company_size ?? "—"}
              </td>
              <td className="px-3 py-2.5">
                <StatusChip kind="account" value={account.status} />
              </td>
              <td className="px-3 py-2.5 tabular-nums text-[color:var(--color-fg-muted)]">
                {formatRelative(account.updated_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
