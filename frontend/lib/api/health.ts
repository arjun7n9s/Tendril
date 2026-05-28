import { api } from "./client";
import type { HealthResponse } from "@/lib/types";

export function getHealth(signal?: AbortSignal) {
  return api.get<HealthResponse>("/health", { signal });
}
