import { api } from "./client";
import type { BriefRead } from "@/lib/types";

export function getAccountBrief(accountId: string, signal?: AbortSignal) {
  return api.get<BriefRead>(`/api/v1/accounts/${accountId}/brief`, { signal });
}

export function regenerateBrief(scanId: string, signal?: AbortSignal) {
  return api.post<BriefRead>(`/api/v1/scans/${scanId}/brief/regenerate`, { signal });
}
