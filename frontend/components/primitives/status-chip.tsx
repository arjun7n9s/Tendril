import { Check, CircleDashed, Clock, OctagonX, Sparkles, TriangleAlert } from "lucide-react";

import { Badge, type BadgeProps } from "@/components/ui/badge";
import type { AccountStatus, OutreachStatus, ScanStatus } from "@/lib/types";
import { cn } from "@/lib/utils/cn";

type StatusChipProps = (
  | { kind: "account"; value: AccountStatus }
  | { kind: "scan"; value: ScanStatus }
  | { kind: "outreach"; value: OutreachStatus }
) & {
  className?: string;
  size?: BadgeProps["size"];
};

const ACCOUNT_LABEL: Record<AccountStatus, string> = {
  target: "Target",
  customer: "Customer",
  former_customer: "Former",
  competitor: "Competitor",
  ignored: "Ignored",
};

const ACCOUNT_VARIANT: Record<AccountStatus, BadgeProps["variant"]> = {
  target: "cobalt",
  customer: "signal",
  former_customer: "evidence",
  competitor: "risk",
  ignored: "outline",
};

const SCAN_LABEL: Record<ScanStatus, string> = {
  queued: "Queued",
  discovering: "Discovering",
  scraping: "Scraping",
  extracting: "Extracting",
  graphing: "Graphing",
  scoring: "Scoring",
  briefing: "Briefing",
  completed: "Completed",
  failed: "Failed",
};

const SCAN_VARIANT: Record<ScanStatus, BadgeProps["variant"]> = {
  queued: "neutral",
  discovering: "cobalt",
  scraping: "cobalt",
  extracting: "cobalt",
  graphing: "graph",
  scoring: "cobalt",
  briefing: "cobalt",
  completed: "signal",
  failed: "risk",
};

const OUTREACH_LABEL: Record<OutreachStatus, string> = {
  pending_review: "Pending review",
  approved: "Approved",
  rejected: "Rejected",
  edited: "Edited",
};

const OUTREACH_VARIANT: Record<OutreachStatus, BadgeProps["variant"]> = {
  pending_review: "evidence",
  approved: "signal",
  rejected: "risk",
  edited: "cobalt",
};

export function StatusChip({ className, size = "md", ...rest }: StatusChipProps) {
  let label: string;
  let variant: BadgeProps["variant"];
  let Icon: typeof Check | null = null;

  if (rest.kind === "account") {
    label = ACCOUNT_LABEL[rest.value];
    variant = ACCOUNT_VARIANT[rest.value];
    if (rest.value === "competitor") Icon = TriangleAlert;
    if (rest.value === "customer") Icon = Sparkles;
  } else if (rest.kind === "scan") {
    label = SCAN_LABEL[rest.value];
    variant = SCAN_VARIANT[rest.value];
    if (rest.value === "completed") Icon = Check;
    else if (rest.value === "failed") Icon = OctagonX;
    else if (rest.value === "queued") Icon = CircleDashed;
    else Icon = Clock;
  } else {
    label = OUTREACH_LABEL[rest.value];
    variant = OUTREACH_VARIANT[rest.value];
    if (rest.value === "approved") Icon = Check;
    if (rest.value === "rejected") Icon = OctagonX;
  }

  return (
    <Badge variant={variant} size={size} className={cn(className)}>
      {Icon ? <Icon className="size-3" /> : null}
      {label}
    </Badge>
  );
}
