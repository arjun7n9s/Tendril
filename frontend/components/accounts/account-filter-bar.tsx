"use client";

import { Search, Sparkles, X } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ACCOUNT_STATUSES, type AccountStatus } from "@/lib/types";
import { cn } from "@/lib/utils/cn";

const STATUS_LABEL: Record<AccountStatus, string> = {
  target: "Target",
  customer: "Customer",
  former_customer: "Former",
  competitor: "Competitor",
  ignored: "Ignored",
};

export function AccountFilterBar() {
  const router = useRouter();
  const params = useSearchParams();

  const urlSearch = params.get("search") ?? "";
  const status = params.get("status") as AccountStatus | null;
  const salesReady = params.get("sales_ready") === "true";

  // The URL is the source of truth. We keep a local mirror keyed by
  // urlSearch so that out-of-band navigation (back/forward, clear)
  // remounts the input with the correct value without an effect.
  const [searchValue, setSearchValue] = useState(urlSearch);

  const setParam = useCallback(
    (key: string, value: string | null) => {
      const next = new URLSearchParams(params.toString());
      if (value === null || value === "") next.delete(key);
      else next.set(key, value);
      const qs = next.toString();
      router.replace(qs ? `?${qs}` : "?");
    },
    [params, router],
  );

  // Debounce local input -> URL.
  useEffect(() => {
    if (searchValue === urlSearch) return;
    const handle = setTimeout(() => {
      setParam("search", searchValue || null);
    }, 250);
    return () => clearTimeout(handle);
  }, [searchValue, urlSearch, setParam]);

  const filtersApplied = useMemo(
    () => Boolean(status || salesReady || urlSearch),
    [status, salesReady, urlSearch],
  );

  return (
    <div key={urlSearch === "" ? "blank" : "filled"} className="flex flex-wrap items-center gap-2">
      <div className="relative">
        <Search
          className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-[color:var(--color-fg-muted)]"
          aria-hidden
        />
        <Input
          value={searchValue}
          onChange={(event) => setSearchValue(event.target.value)}
          placeholder="Search by name or domain"
          className="h-8 w-64 pl-8 text-[13px]"
        />
      </div>

      <div className="flex flex-wrap items-center gap-1">
        {ACCOUNT_STATUSES.map((option) => {
          const active = status === option;
          return (
            <button
              key={option}
              type="button"
              onClick={() => setParam("status", active ? null : option)}
              className={cn(
                "inline-flex h-7 items-center rounded-[var(--radius-button)] border px-2 text-[12px] transition-colors",
                active
                  ? "border-[color:var(--color-fg-primary)] bg-[color:var(--color-fg-primary)] text-[color:var(--color-surface)]"
                  : "border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] text-[color:var(--color-fg-secondary)] hover:bg-[color:var(--color-raised)]",
              )}
            >
              {STATUS_LABEL[option]}
            </button>
          );
        })}
      </div>

      <button
        type="button"
        onClick={() => setParam("sales_ready", salesReady ? null : "true")}
        className={cn(
          "inline-flex h-7 items-center gap-1.5 rounded-[var(--radius-button)] border px-2 text-[12px] transition-colors",
          salesReady
            ? "border-[color:color-mix(in_oklab,var(--color-signal)_30%,transparent)] bg-[color:var(--color-signal-soft)] text-[color:var(--color-signal)]"
            : "border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] text-[color:var(--color-fg-secondary)] hover:bg-[color:var(--color-raised)]",
        )}
      >
        <Sparkles className="size-3" aria-hidden />
        Sales-ready only
      </button>

      {filtersApplied ? (
        <Button
          variant="ghost"
          size="sm"
          className="h-7 px-2 text-[12px] text-[color:var(--color-fg-secondary)]"
          onClick={() => {
            setSearchValue("");
            router.replace("?");
          }}
        >
          <X className="size-3" aria-hidden />
          Clear
        </Button>
      ) : null}
    </div>
  );
}
