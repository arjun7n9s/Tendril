"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { toast } from "sonner";

import { importsApi } from "@/lib/api";
import { COPY } from "@/lib/copy";

const SESSION_FLAG = "tendril:demo-seed-primed";

async function fetchSeedFile(): Promise<File | null> {
  try {
    const res = await fetch("/seed_demo.csv", { cache: "force-cache" });
    if (!res.ok) return null;
    const blob = await res.blob();
    return new File([blob], "seed_demo.csv", { type: "text/csv" });
  } catch {
    return null;
  }
}

/**
 * Auto-primes the demo seed when /accounts is empty on first paint.
 *
 * Decision locked in kiro/kiro-frontend-requirements-checklist.md A5: the demo
 * never opens to an empty app, but the user can still re-run a manual
 * import at /imports.
 */
export function useAutoPrimeSeed(opts: { isEmpty: boolean; isReady: boolean }) {
  const { isEmpty, isReady } = opts;
  const fired = useRef(false);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async () => {
      const file = await fetchSeedFile();
      if (!file) throw new Error("seed_demo.csv missing from /public");
      return importsApi.importSeedCsv(file, "seed_demo.csv");
    },
    onSuccess: () => {
      sessionStorage.setItem(SESSION_FLAG, "1");
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      toast.success(COPY.demo.primedToast, { description: COPY.demo.primedDescription });
    },
    onError: (err) => {
      // Soft-fail: the empty state remains usable, judges can drag-drop on /imports.
      // We only log because the auto-prime is a UX nicety, not a hard requirement.
      console.warn("[auto-prime-seed] failed:", err);
    },
  });

  useEffect(() => {
    if (!isReady || !isEmpty || fired.current) return;
    if (typeof window === "undefined") return;
    if (sessionStorage.getItem(SESSION_FLAG) === "1") return;
    fired.current = true;
    mutation.mutate();
  }, [isReady, isEmpty, mutation]);

  return { isPriming: mutation.isPending };
}
