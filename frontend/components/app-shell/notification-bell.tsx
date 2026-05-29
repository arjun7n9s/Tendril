"use client";

import { Bell, CheckCheck } from "lucide-react";
import Link from "next/link";

import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@radix-ui/react-popover";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
} from "@/lib/hooks/use-notifications";
import type { NotificationRead } from "@/lib/types";
import { cn } from "@/lib/utils/cn";
import { formatRelative } from "@/lib/utils/dates";

export function NotificationBell() {
  const { data } = useNotifications();
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllNotificationsRead();

  const items = data?.items ?? [];
  const unread = data?.unread ?? 0;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          aria-label={`Notifications${unread ? `, ${unread} unread` : ""}`}
          className={cn(
            "relative inline-flex size-8 items-center justify-center rounded-[var(--radius-button)] border border-border bg-raised/50 text-fg-secondary transition-colors duration-150",
            "hover:bg-raised hover:text-fg-primary",
            "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[color:var(--color-fg-primary)]",
          )}
        >
          <Bell className="size-4" aria-hidden />
          {unread > 0 ? (
            <span className="absolute -right-1 -top-1 grid min-w-4 place-items-center rounded-full bg-[color:var(--color-signal)] px-1 text-[10px] font-semibold leading-4 text-white">
              {unread > 9 ? "9+" : unread}
            </span>
          ) : null}
        </button>
      </PopoverTrigger>
      <PopoverContent
        align="end"
        sideOffset={8}
        className="z-50 w-[360px] rounded-[var(--radius-card)] border border-border bg-surface p-0 shadow-raised"
      >
        <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
          <span className="text-[13px] font-semibold text-fg-primary">Notifications</span>
          {unread > 0 ? (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 gap-1 px-1.5 text-[11px]"
              onClick={() => markAll.mutate(undefined)}
            >
              <CheckCheck className="size-3" aria-hidden />
              Mark all read
            </Button>
          ) : null}
        </div>
        {items.length === 0 ? (
          <div className="px-4 py-10 text-center text-[12px] text-fg-muted">
            You&rsquo;re all caught up.
          </div>
        ) : (
          <ScrollArea className="max-h-[380px]">
            <ul className="flex flex-col">
              {items.map((n) => (
                <NotificationRow key={n.id} notification={n} onRead={() => markRead.mutate(n.id)} />
              ))}
            </ul>
          </ScrollArea>
        )}
      </PopoverContent>
    </Popover>
  );
}

function NotificationRow({
  notification,
  onRead,
}: {
  notification: NotificationRead;
  onRead: () => void;
}) {
  const body = (
    <div
      className={cn(
        "flex flex-col gap-1 border-b border-border-default px-4 py-2.5 transition-colors last:border-b-0 hover:bg-raised",
        !notification.read && "bg-cobalt-soft/30",
      )}
    >
      <div className="flex items-start gap-2">
        {!notification.read ? (
          <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-[color:var(--color-cobalt)]" />
        ) : (
          <span className="mt-1.5 size-1.5 shrink-0" />
        )}
        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
          <span className="text-[12.5px] font-medium leading-snug text-fg-primary">
            {notification.title}
          </span>
          {notification.body ? (
            <span className="text-[11.5px] leading-snug text-fg-secondary">
              {notification.body}
            </span>
          ) : null}
          <span className="text-[10.5px] text-fg-muted">
            {formatRelative(notification.created_at)}
          </span>
        </div>
      </div>
    </div>
  );

  if (notification.link) {
    return (
      <li>
        <Link href={notification.link} onClick={onRead} className="block">
          {body}
        </Link>
      </li>
    );
  }
  return (
    <li>
      <button type="button" onClick={onRead} className="block w-full text-left">
        {body}
      </button>
    </li>
  );
}
