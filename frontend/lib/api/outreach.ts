import { api } from "./client";
import type { OutreachList, OutreachPatch, OutreachRead, OutreachReject } from "@/lib/types";

export function listPendingOutreach(allHistory = false, signal?: AbortSignal) {
  return api.get<OutreachList>("/api/v1/outreach/pending", {
    params: { all_history: allHistory },
    signal,
  });
}

export function getOutreachDraft(draftId: string, signal?: AbortSignal) {
  return api.get<OutreachRead>(`/api/v1/outreach/${draftId}`, { signal });
}

export function approveOutreachDraft(draftId: string, signal?: AbortSignal) {
  return api.post<OutreachRead>(`/api/v1/outreach/${draftId}/approve`, { signal });
}

export function rejectOutreachDraft(
  draftId: string,
  body: OutreachReject = {},
  signal?: AbortSignal,
) {
  return api.post<OutreachRead>(`/api/v1/outreach/${draftId}/reject`, { body, signal });
}

export function patchOutreachDraft(
  draftId: string,
  body: OutreachPatch,
  signal?: AbortSignal,
) {
  return api.patch<OutreachRead>(`/api/v1/outreach/${draftId}`, { body, signal });
}
