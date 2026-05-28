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
      "bg-fg-primary/95 text-surface border border-fg-primary/20 shadow-md",
    icon: Building2,
    iconClass: "text-surface",
  },
  signal: {
    container:
      "bg-cobalt-soft/80 backdrop-blur-md text-cobalt border border-cobalt/25 shadow-glow-cobalt",
    icon: Radar,
    iconClass: "text-cobalt",
  },
  evidence: {
    container:
      "bg-evidence-soft/80 backdrop-blur-md text-evidence border border-evidence/25 shadow-glow-amber",
    icon: FileSearch,
    iconClass: "text-evidence",
  },
  tech: {
    container:
      "bg-graph-soft/80 backdrop-blur-md text-graph border border-graph/25",
    icon: Cpu,
    iconClass: "text-graph",
  },
  competitor: {
    container:
      "bg-risk-soft/80 backdrop-blur-md text-risk border border-risk/25",
    icon: Crosshair,
    iconClass: "text-risk",
  },
  icp: {
    container:
      "bg-signal-soft/80 backdrop-blur-md text-signal border border-signal/25 shadow-glow-emerald",
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
        "flex max-w-[200px] items-start gap-2 rounded-[var(--radius-card)] px-2.5 py-2 transition-all duration-300 ease-out hover:scale-[1.03]",
        style.container,
        node.href ? "hover:shadow-raised hover:-translate-y-0.5" : "",
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
