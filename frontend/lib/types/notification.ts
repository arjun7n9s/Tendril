// Source: backend/app/schemas/notification.py and backend/app/models/enums.py

import type { Timestamped } from "./common";

export const NOTIFICATION_TYPES = [
  "media_scan_completed",
  "media_scan_failed",
  "conversation_signal",
  "score_change",
  "new_source",
  "info",
] as const;
export type NotificationType = (typeof NOTIFICATION_TYPES)[number];

export type NotificationRead = Timestamped & {
  id: string;
  account_id?: string | null;
  notification_type: NotificationType;
  title: string;
  body?: string | null;
  link?: string | null;
  read: boolean;
  metadata_json?: Record<string, unknown> | null;
};

export type NotificationList = {
  items: NotificationRead[];
  total: number;
  unread: number;
};
