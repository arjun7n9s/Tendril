import { api } from "./client";
import type {
  ConversationSignalList,
  MediaScanCreateRequest,
  MediaScanCreateResponse,
  MediaScanEventList,
  MediaScanRead,
  MediaSourceRead,
  TranscriptRead,
} from "@/lib/types";

export function createMediaScan(
  accountId: string,
  body: MediaScanCreateRequest = {},
  signal?: AbortSignal,
) {
  return api.post<MediaScanCreateResponse>(`/api/v1/accounts/${accountId}/media-scans`, {
    body: {
      mode: body.mode ?? "mock",
      max_sources: body.max_sources ?? 3,
      force_refresh: body.force_refresh ?? false,
    },
    signal,
  });
}

export function getMediaScan(scanId: string, signal?: AbortSignal) {
  return api.get<MediaScanRead>(`/api/v1/media-scans/${scanId}`, { signal });
}

export function getMediaScanEvents(scanId: string, afterSequence = 0, signal?: AbortSignal) {
  return api.get<MediaScanEventList>(`/api/v1/media-scans/${scanId}/events`, {
    params: { after_sequence: afterSequence, limit: 500 },
    signal,
  });
}

export function resumeMediaScan(scanId: string, signal?: AbortSignal) {
  return api.post<MediaScanCreateResponse>(`/api/v1/media-scans/${scanId}/resume`, { signal });
}

export function getAccountMediaSources(accountId: string, signal?: AbortSignal) {
  return api.get<MediaSourceRead[]>(`/api/v1/accounts/${accountId}/media-sources`, { signal });
}

export function getAccountConversationSignals(accountId: string, signal?: AbortSignal) {
  return api.get<ConversationSignalList>(
    `/api/v1/accounts/${accountId}/conversation-signals`,
    { signal },
  );
}

export function getTranscript(transcriptId: string, signal?: AbortSignal) {
  return api.get<TranscriptRead>(`/api/v1/transcripts/${transcriptId}`, { signal });
}
