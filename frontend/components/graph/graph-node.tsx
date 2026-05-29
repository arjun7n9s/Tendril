"use client";

import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Building2, Cpu, Crosshair, FileSearch, Radar, Target } from "lucide-react";

import type { GraphNodeData } from "./graph-derive";
import { cn } from "@/lib/utils/cn";

const KIND_STYLES: Record<
  GraphNodeData["kind"],
  { container: string; icon: React.ComponentType<{ className?: string }>; iconClass: string }
> = {
  account: {
    container:
      "bg-fg-primary text-surface border-fg-primary shadow-flat",
    icon: Building2,
    iconClass: "text-surface",
  },
  signal: {
    container:
      "bg-surface text-fg-primary border-border hover:border-cobalt/40 shadow-flat",
    icon: Radar,
    iconClass: "text-cobalt",
  },
  evidence: {
    container:
      "bg-surface text-fg-primary border-border hover:border-evidence/40 shadow-flat",
    icon: FileSearch,
    iconClass: "text-evidence",
  },
  tech: {
    container:
      "bg-surface text-fg-primary border-border hover:border-graph/40 shadow-flat",
    icon: Cpu,
    iconClass: "text-graph",
  },
  competitor: {
    container:
      "bg-surface text-fg-primary border-border hover:border-risk/40 shadow-flat",
    icon: Crosshair,
    iconClass: "text-risk",
  },
  icp: {
    container:
      "bg-surface text-fg-primary border-border hover:border-signal/40 shadow-flat",
    icon: Target,
    iconClass: "text-signal",
  },
};

export function TendrilGraphNode({ data }: NodeProps) {
  const node = data as GraphNodeData;
  const style = KIND_STYLES[node.kind];
  const Icon = style.icon;

  const Wrapper: React.ElementType = node.href ? "a" : "div";
  const wrapperProps = node.href
    ? { href: node.href, target: "_blank" as const, rel: "noreferrer" }
    : {};

  return (
    <Wrapper
      {...wrapperProps}
      className={cn(
        "flex max-w-[200px] items-start gap-2.5 rounded-[var(--radius-card)] px-3 py-2.5 transition-all duration-150 ease-out",
        style.container,
        node.href ? "hover:shadow-raised hover:border-border-strong" : "",
      )}
    >
      <Handle type="target" position={Position.Left} className="opacity-0" />
      <span className="mt-0.5 flex-shrink-0">
        <Icon className={cn("size-3.5", style.iconClass)} aria-hidden />
      </span>
      <span className="flex min-w-0 flex-col">
        <span className="line-clamp-2 text-[12px] font-medium leading-tight">
          {node.label}
        </span>
        {node.sublabel ? (
          <span className="truncate text-[10px] tracking-[0.04em] uppercase opacity-80">
            {node.sublabel}
          </span>
        ) : null}
      </span>
      <Handle type="source" position={Position.Right} className="opacity-0" />
    </Wrapper>
  );
}
