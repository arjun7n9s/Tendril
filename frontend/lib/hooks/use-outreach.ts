"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { ApiError, outreachApi } from "@/lib/api";
import { COPY } from "@/lib/copy";
import type { OutreachPatch, OutreachTone } from "@/lib/types";

export function usePendingOutreach(allHistory = false) {
  return useQuery({
    queryKey: ["outreach-pending", { allHistory }],
    queryFn: ({ signal }) => outreachApi.listPendingOutreach(allHistory, signal),
  });
}

export function useOutreachDraft(draftId: string | null) {
  return useQuery({
    queryKey: ["outreach", draftId],
    queryFn: ({ signal }) => outreachApi.getOutreachDraft(draftId!, signal),
    enabled: Boolean(draftId),
  });
}

export function useApproveDraft(draftId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => outreachApi.approveOutreachDraft(draftId),
    onSuccess: (data) => {
      toast.success(COPY.outreach.approvedToast);
      queryClient.setQueryData(["outreach", draftId], data);
      queryClient.invalidateQueries({ queryKey: ["outreach-pending"] });
    },
    onError: (err) => {
      toast.error("Could not approve draft", {
        description: err instanceof ApiError ? err.message : undefined,
      });
    },
  });
}

export function useRejectDraft(draftId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (feedback?: string) =>
      outreachApi.rejectOutreachDraft(draftId, feedback ? { feedback } : {}),
    onSuccess: (data) => {
      toast.success(COPY.outreach.rejectedToast);
      queryClient.setQueryData(["outreach", draftId], data);
      queryClient.invalidateQueries({ queryKey: ["outreach-pending"] });
    },
    onError: (err) => {
      toast.error("Could not reject draft", {
        description: err instanceof ApiError ? err.message : undefined,
      });
    },
  });
}

export function useEditDraft(draftId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (patch: OutreachPatch) => outreachApi.patchOutreachDraft(draftId, patch),
    onSuccess: (data) => {
      toast.success(COPY.outreach.editedToast);
      queryClient.setQueryData(["outreach", draftId], data);
      queryClient.invalidateQueries({ queryKey: ["outreach-pending"] });
    },
    onError: (err) => {
      toast.error("Could not save draft", {
        description: err instanceof ApiError ? err.message : undefined,
      });
    },
  });
}

export function useRegenerateDraft(draftId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (tone: OutreachTone) =>
      outreachApi.regenerateOutreachDraft(draftId, { tone }),
    onSuccess: (data) => {
      toast.success(COPY.outreach.regeneratedToast);
      queryClient.setQueryData(["outreach", draftId], data);
      queryClient.invalidateQueries({ queryKey: ["outreach-pending"] });
    },
    onError: (err) => {
      toast.error("Could not rewrite draft", {
        description: err instanceof ApiError ? err.message : undefined,
      });
    },
  });
}
