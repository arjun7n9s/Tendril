"use client";

import {
  Background,
  BackgroundVariant,
  Controls,
  type Edge,
  MiniMap,
  type Node,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";
import { useMemo } from "react";

import "@xyflow/react/dist/style.css";

import type { AccountRead, BriefRead, SignalRead } from "@/lib/types";

import { deriveAccountGraph, type GraphNodeData } from "./graph-derive";
import { TendrilGraphNode } from "./graph-node";

const NODE_TYPES = { tendril: TendrilGraphNode };

type AccountKnowledgeGraphProps = {
  account: AccountRead;
  signals: SignalRead[];
  brief: BriefRead | null;
};

export function AccountKnowledgeGraph(props: AccountKnowledgeGraphProps) {
  return (
    <ReactFlowProvider>
      <Inner {...props} />
    </ReactFlowProvider>
  );
}

function Inner({ account, signals, brief }: AccountKnowledgeGraphProps) {
  const initial = useMemo(() => deriveAccountGraph({ account, signals, brief }), [
    account,
    signals,
    brief,
  ]);

  const [nodes, , onNodesChange] = useNodesState<Node<GraphNodeData>>(initial.nodes);
  const [edges, , onEdgesChange] = useEdgesState<Edge>(initial.edges);

  return (
    <div
      role="figure"
      aria-label={`Knowledge graph for ${account.name}`}
      className="rounded-[var(--radius-card)] border border-border-default bg-surface shadow-flat relative overflow-hidden transition-all duration-200 hover:border-border-strong"
      style={{ height: 540 }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={NODE_TYPES}
        fitView
        fitViewOptions={{ padding: 0.25 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable
        nodesConnectable={false}
        edgesFocusable={false}
        defaultEdgeOptions={{
          style: { stroke: "var(--color-border-strong)", strokeWidth: 1.25 },
          labelStyle: {
            fontSize: 10,
            fill: "var(--color-fg-muted)",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
          },
          labelBgStyle: { fill: "var(--color-canvas)", opacity: 0.85 },
          labelBgPadding: [4, 2],
          labelBgBorderRadius: 4,
        }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={18}
          size={1}
          color="var(--color-border-default)"
        />
        <Controls
          position="bottom-right"
          showInteractive={false}
          className="!rounded-md !border !border-border-default !bg-surface !text-fg-secondary !shadow-flat"
        />
        <MiniMap
          pannable
          zoomable
          className="!rounded-md !border !border-border-default !bg-surface !shadow-flat"
          maskColor="rgba(0, 0, 0, 0.05)"
          nodeColor={(node) => {
            const data = node.data as GraphNodeData | undefined;
            switch (data?.kind) {
              case "account":
                return "var(--color-fg-primary)";
              case "signal":
                return "var(--color-cobalt)";
              case "evidence":
                return "var(--color-evidence)";
              case "tech":
                return "var(--color-graph)";
              case "competitor":
                return "var(--color-risk)";
              case "icp":
                return "var(--color-signal)";
              default:
                return "var(--color-border-strong)";
            }
          }}
        />
      </ReactFlow>
    </div>
  );
}
