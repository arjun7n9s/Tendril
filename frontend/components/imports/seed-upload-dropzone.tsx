"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, UploadCloud } from "lucide-react";
import Link from "next/link";
import { useCallback, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { ApiError, importsApi } from "@/lib/api";
import { COPY } from "@/lib/copy";
import type { SeedImportResponse } from "@/lib/types";
import { cn } from "@/lib/utils/cn";

const REQUIRED_COLUMNS = [
  "row_type",
  "name",
  "domain",
  "industry",
  "company_size",
  "region",
  "status",
];

export function SeedUploadDropzone() {
  const queryClient = useQueryClient();
  const [isDragging, setIsDragging] = useState(false);
  const [result, setResult] = useState<SeedImportResponse | null>(null);

  const mutation = useMutation({
    mutationFn: async (file: File) => importsApi.importSeedCsv(file, file.name),
    onSuccess: (data) => {
      setResult(data);
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      sessionStorage.setItem("tendril:demo-seed-primed", "1");
      toast.success(COPY.imports.success, {
        description: `${data.accounts_created} accounts · ${data.people_created} people · ${data.icp_profiles_created} ICP profiles`,
      });
    },
    onError: (err) => {
      const message = err instanceof ApiError ? err.message : "Import failed";
      toast.error("Import failed", { description: message });
    },
  });

  const handleFile = useCallback(
    (file: File | null) => {
      if (!file) return;
      if (!file.name.toLowerCase().endsWith(".csv")) {
        toast.error("Only .csv files are supported");
        return;
      }
      mutation.mutate(file);
    },
    [mutation],
  );

  const handleDemoLoad = useCallback(async () => {
    try {
      const res = await fetch("/seed_demo.csv", { cache: "force-cache" });
      if (!res.ok) throw new Error("seed_demo.csv missing");
      const blob = await res.blob();
      handleFile(new File([blob], "seed_demo.csv", { type: "text/csv" }));
    } catch (err) {
      toast.error("Could not load demo seed", {
        description: err instanceof Error ? err.message : undefined,
      });
    }
  }, [handleFile]);

  return (
    <div className="flex flex-col gap-4">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          handleFile(event.dataTransfer.files[0] ?? null);
        }}
        className={cn(
          "flex flex-col items-center justify-center gap-3 rounded-[var(--radius-card)] border-2 border-dashed bg-[color:var(--color-surface)] px-6 py-10 text-center transition-colors",
          isDragging
            ? "border-[color:var(--color-signal)] bg-[color:var(--color-signal-soft)]"
            : "border-[color:var(--color-border-default)]",
        )}
      >
        <span className="grid size-10 place-items-center rounded-full bg-[color:var(--color-raised)] text-[color:var(--color-fg-secondary)]">
          {mutation.isPending ? (
            <Loader2 className="size-5 animate-spin" aria-hidden />
          ) : (
            <UploadCloud className="size-5" aria-hidden />
          )}
        </span>
        <div className="flex flex-col gap-1">
          <h3 className="text-[15px] font-semibold text-[color:var(--color-fg-primary)]">
            Drop a CRM CSV here
          </h3>
          <p className="text-[13px] text-[color:var(--color-fg-secondary)]">
            Or browse for a file. We will normalize accounts, people, and ICP profiles.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button asChild variant="primary" size="sm">
            <label className="cursor-pointer">
              <span>Browse file</span>
              <input
                type="file"
                accept=".csv,text/csv"
                className="sr-only"
                onChange={(event) => handleFile(event.target.files?.[0] ?? null)}
                disabled={mutation.isPending}
              />
            </label>
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleDemoLoad}
            disabled={mutation.isPending}
          >
            Load demo seed
          </Button>
        </div>
      </div>

      <div className="rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] p-4">
        <h4 className="text-[12px] font-semibold tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
          Required columns
        </h4>
        <p className="mt-1 text-[13px] text-[color:var(--color-fg-secondary)]">
          The seed CSV is row-typed: each row is one of <code className="font-mono">account</code>,
          <code className="font-mono"> person</code>, or <code className="font-mono">icp</code>.
        </p>
        <ul className="mt-3 grid grid-cols-2 gap-1.5 sm:grid-cols-4">
          {REQUIRED_COLUMNS.map((column) => (
            <li
              key={column}
              className="rounded-[var(--radius-chip)] bg-[color:var(--color-raised)] px-2 py-1 font-mono text-[12px] text-[color:var(--color-fg-secondary)]"
            >
              {column}
            </li>
          ))}
        </ul>
      </div>

      {result ? (
        <div className="rounded-[var(--radius-card)] border border-[color:color-mix(in_oklab,var(--color-signal)_30%,transparent)] bg-[color:var(--color-signal-soft)] p-4">
          <h4 className="text-[14px] font-semibold text-[color:var(--color-signal)]">
            Imported successfully
          </h4>
          <ul className="mt-2 grid grid-cols-2 gap-1 text-[13px] text-[color:var(--color-fg-primary)] sm:grid-cols-3">
            <li>{result.accounts_created} accounts created</li>
            <li>{result.accounts_updated} accounts updated</li>
            <li>{result.people_created} people created</li>
            <li>{result.people_updated} people updated</li>
            <li>{result.icp_profiles_created} ICP profiles created</li>
            <li>{result.icp_profiles_updated} ICP profiles updated</li>
          </ul>
          {result.warnings.length > 0 ? (
            <details className="mt-3 text-[12px] text-[color:var(--color-fg-secondary)]">
              <summary className="cursor-pointer font-medium text-[color:var(--color-fg-primary)]">
                {result.warnings.length} warning{result.warnings.length === 1 ? "" : "s"}
              </summary>
              <ul className="mt-1 list-inside list-disc space-y-0.5">
                {result.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </details>
          ) : null}
          <div className="mt-3">
            <Button asChild size="sm">
              <Link href="/accounts">Open accounts</Link>
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
