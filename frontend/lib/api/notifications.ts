import { api } from "./client";
import type { NotificationList, NotificationRead } from "@/lib/types";

export function listNotifications(
  params: { unreadOnly?: boolean; accountId?: string; limit?: number } = {},
  signal?: AbortSignal,
) {
  return api.get<NotificationList>("/api/v1/notifications", {
    params: {
      unread_only: params.unreadOnly,
      account_id: params.accountId,
      limit: params.limit,
    },
    signal,
  });
}

export function markNotificationRead(notificationId: string, signal?: AbortSignal) {
  return api.post<NotificationRead>(`/api/v1/notifications/${notificationId}/read`, { signal });
}

export function markAllNotificationsRead(accountId?: string, signal?: AbortSignal) {
  return api.post<{ updated: number }>("/api/v1/notifications/read-all", {
    params: { account_id: accountId },
    signal,
  });
}
