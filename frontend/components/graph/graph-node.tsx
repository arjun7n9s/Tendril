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
      "bg-[color:var(--color-fg-primary)] text-[color:var(--color-surface)] border border-[color:var(--color-fg-primary)]",
    icon: Building2,
    iconClass: "text-[color:var(--color-surface)]",
  },
  signal: {
    container:
      "bg-[color:var(--color-cobalt-soft)] text-[color:var(--color-cobalt)] border border-[color:color-mix(in_oklab,var(--color-cobalt)_30%,transparent)]",
    icon: Radar,
    iconClass: "text-[color:var(--color-cobalt)]",
  },
  evidence: {
    container:
      "bg-[color:var(--color-evidence-soft)] text-[color:var(--color-evidence)] border border-[color:color-mix(in_oklab,var(--color-evidence)_30%,transparent)]",
    icon: FileSearch,
    iconClass: "text-[color:var(--color-evidence)]",
  },
  tech: {
    container:
      "bg-[color:var(--color-graph-soft)] text-[color:var(--color-graph)] border border-[color:color-mix(in_oklab,var(--color-graph)_30%,transparent)]",
    icon: Cpu,
    iconClass: "text-[color:var(--color-graph)]",
  },
  competitor: {
    container:
      "bg-[color:var(--color-risk-soft)] text-[color:var(--color-risk)] border border-[color:color-mix(in_oklab,var(--color-risk)_30%,transparent)]",
    icon: Crosshair,
    iconClass: "text-[color:var(--color-risk)]",
  },
  icp: {
    container:
      "bg-[color:var(--color-signal-soft)] text-[color:var(--color-signal)] border border-[color:color-mix(in_oklab,var(--color-signal)_30%,transparent)]",
    icon: Target,
    iconClass: "text-[color:var(--color-signal)]",
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
        "flex max-w-[200px] items-start gap-2 rounded-[var(--radius-card)] px-2.5 py-2 shadow-[var(--shadow-flat)]",
        style.container,
        node.href ? "hover:shadow-[var(--shadow-raised)]" : "",
      )}
    >
      <Handle type="target" position={Position.Left} className="opacity-0" />
      <span className="mt-0.5">
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
