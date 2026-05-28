import { api } from "./client";
import type { SeedImportResponse } from "@/lib/types";

export function importSeedCsv(file: File | Blob, filename = "seed.csv", signal?: AbortSignal) {
  const formData = new FormData();
  formData.append("file", file, filename);
  return api.post<SeedImportResponse>("/api/v1/import/seed", {
    formData,
    signal,
    timeoutMs: 60_000,
  });
}
