"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Loader2, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { IntegrationStatus } from "./integration-status";
import { ModeChip } from "./mode-chip";

import { MonogramTile } from "@/components/primitives/monogram-tile";
import { StatusChip } from "@/components/primitives/status-chip";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { accountsApi } from "@/lib/api";
import type { AccountRead } from "@/lib/types";
import { cn } from "@/lib/utils/cn";

type TopCommandBarProps = {
  title: string;
  subtitle?: string;
  primaryAction?: React.ReactNode;
  /** Optional: render a contextual filter or tab strip beneath the title row. */
  meta?: React.ReactNode;
};

export function TopCommandBar({ title, subtitle, primaryAction, meta }: TopCommandBarProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchValue, setSearchValue] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    const handle = window.setTimeout(() => setDebouncedSearch(searchValue.trim()), 180);
    return () => window.clearTimeout(handle);
  }, [searchValue]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    if (!searchOpen) return;
    const handle = window.setTimeout(() => inputRef.current?.focus(), 0);
    return () => window.clearTimeout(handle);
  }, [searchOpen]);

  const searchQuery = useQuery({
    queryKey: ["command-search-accounts", debouncedSearch],
    queryFn: ({ signal }) =>
      accountsApi.listAccounts(
        {
          search: debouncedSearch || undefined,
          limit: 8,
          offset: 0,
        },
        signal,
      ),
    enabled: searchOpen,
  });

  const accounts = useMemo<AccountRead[]>(
    () => searchQuery.data?.items ?? [],
    [searchQuery.data],
  );

  const openAccount = (accountId: string) => {
    setSearchOpen(false);
    setSearchValue("");
    router.push(`/accounts/${accountId}`);
  };

  return (
    <header
      className={cn(
        "sticky top-0 z-30 flex flex-col gap-3 border-b border-border bg-surface px-6 py-3",
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-col gap-0.5">
          <h1 className="text-[17px] leading-tight font-semibold text-fg-primary">
            {title}
          </h1>
          {subtitle ? <p className="text-[11px] text-fg-muted">{subtitle}</p> : null}
        </div>
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <button
            type="button"
            className={cn(
              "hidden h-8 items-center gap-2 rounded-[var(--radius-button)] border border-border bg-raised/50 px-2.5 text-[12px] text-fg-muted transition-colors duration-150 md:inline-flex",
              "hover:bg-raised hover:text-fg-primary",
              "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[color:var(--color-fg-primary)]",
            )}
            aria-label="Search accounts"
            onClick={() => setSearchOpen(true)}
          >
            <Search className="size-3.5" aria-hidden />
            <span>Search...</span>
            <kbd className="hidden h-5 items-center rounded border border-border bg-canvas px-1 text-[10px] font-medium text-fg-muted xl:inline-flex">
              Ctrl K
            </kbd>
          </button>
          <ModeChip />
          <div className="hidden lg:flex">
            <IntegrationStatus />
          </div>
          {primaryAction ? <div className="ml-auto sm:ml-2">{primaryAction}</div> : null}
        </div>
      </div>
      {meta ? <div>{meta}</div> : null}
      <Dialog open={searchOpen} onOpenChange={setSearchOpen}>
        <DialogContent className="top-[18vh] max-h-[78vh] max-w-[620px] translate-y-0 gap-0 overflow-hidden p-0">
          <div className="border-b border-border px-4 pt-4 pb-3">
            <DialogTitle>Search Tendril</DialogTitle>
            <DialogDescription>
              Find accounts by name, domain, industry, or current status.
            </DialogDescription>
          </div>
          <div className="relative border-b border-border px-4 py-3">
            <Search
              className="pointer-events-none absolute top-1/2 left-6 size-4 -translate-y-1/2 text-fg-muted"
              aria-hidden
            />
            <Input
              ref={inputRef}
              value={searchValue}
              onChange={(event) => setSearchValue(event.target.value)}
              placeholder="Search accounts..."
              className="h-10 pl-9 pr-10 text-[14px]"
            />
            {searchQuery.isFetching ? (
              <Loader2
                className="absolute top-1/2 right-6 size-4 -translate-y-1/2 animate-spin text-fg-muted"
                aria-label="Loading search results"
              />
            ) : null}
          </div>
          <div className="max-h-[420px] overflow-y-auto p-2">
            {searchQuery.isLoading ? (
              <SearchLoadingRows />
            ) : searchQuery.isError ? (
              <div className="px-3 py-8 text-center text-[13px] text-fg-secondary">
                Search is unavailable. Check the backend connection and try again.
              </div>
            ) : accounts.length === 0 ? (
              <div className="px-3 py-8 text-center text-[13px] text-fg-secondary">
                {debouncedSearch
                  ? "No matching accounts found."
                  : "Start typing or pick from recent accounts."}
              </div>
            ) : (
              <div className="flex flex-col gap-1">
                {accounts.map((account) => (
                  <button
                    key={account.id}
                    type="button"
                    onClick={() => openAccount(account.id)}
                    className="group flex w-full items-center justify-between gap-3 rounded-[7px] px-3 py-2 text-left transition-colors hover:bg-raised focus-visible:bg-raised focus-visible:outline-none"
                  >
                    <span className="flex min-w-0 items-center gap-3">
                      <MonogramTile name={account.name} seed={account.id} size="md" />
                      <span className="flex min-w-0 flex-col">
                        <span className="truncate text-[13px] font-medium text-fg-primary">
                          {account.name}
                        </span>
                        <span className="truncate text-[12px] text-fg-muted">
                          {[account.domain, account.industry].filter(Boolean).join(" - ") ||
                            "No domain yet"}
                        </span>
                      </span>
                    </span>
                    <span className="flex shrink-0 items-center gap-2">
                      <StatusChip kind="account" value={account.status} />
                      <ArrowRight
                        className="size-3.5 text-fg-muted opacity-0 transition-opacity group-hover:opacity-100"
                        aria-hidden
                      />
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </header>
  );
}

function SearchLoadingRows() {
  return (
    <div className="flex flex-col gap-1">
      {Array.from({ length: 5 }).map((_, index) => (
        <div key={index} className="flex items-center gap-3 rounded-[7px] px-3 py-2">
          <Skeleton className="size-8 rounded-[6px]" />
          <div className="flex flex-1 flex-col gap-1.5">
            <Skeleton className="h-3 w-40" />
            <Skeleton className="h-2.5 w-56" />
          </div>
          <Skeleton className="h-5 w-16 rounded-[999px]" />
        </div>
      ))}
    </div>
  );
}
