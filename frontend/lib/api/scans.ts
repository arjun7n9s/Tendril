import { api } from "./client";
import type {
  EvidenceRead,
  ScanCreateRequest,
  ScanCreateResponse,
  ScanEventList,
  ScanRead,
  SourceRead,
} from "@/lib/types";

export function createScan(
  accountId: string,
  body: ScanCreateRequest = {},
  signal?: AbortSignal,
) {
  return api.post<ScanCreateResponse>(`/api/v1/accounts/${accountId}/scans`, {
    body: {
      scan_type: body.scan_type ?? "account_watchtower",
      mode: body.mode ?? "mock",
      max_sources: body.max_sources ?? 8,
      force_refresh: body.force_refresh ?? false,
    },
    signal,
  });
}

export function getScan(scanId: string, signal?: AbortSignal) {
  return api.get<ScanRead>(`/api/v1/scans/${scanId}`, { signal });
}

export function getScanEvents(scanId: string, afterSequence = 0, signal?: AbortSignal) {
  return api.get<ScanEventList>(`/api/v1/scans/${scanId}/events`, {
    params: { after_sequence: afterSequence, limit: 500 },
    signal,
  });
}

export function getScanSources(scanId: string, signal?: AbortSignal) {
  return api.get<SourceRead[]>(`/api/v1/scans/${scanId}/sources`, { signal });
}

export function getScanEvidence(scanId: string, signal?: AbortSignal) {
  return api.get<EvidenceRead[]>(`/api/v1/scans/${scanId}/evidence`, { signal });
}
