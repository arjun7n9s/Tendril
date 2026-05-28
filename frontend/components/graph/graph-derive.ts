// Client-derived knowledge graph for an account.
//
// Decision sourced from frontend_requirements_checklist.md J: Phase 1
// graph derives nodes/edges from existing payloads (account,
// signals, brief.key_evidence) instead of waiting on a dedicated
// /accounts/{id}/graph backend endpoint. We can revisit later if
// relationship ranking needs server-side help.

import type { Edge, Node } from "@xyflow/react";

import type { AccountRead, BriefRead, SignalRead, SignalType } from "@/lib/types";

export type GraphNodeType = "account" | "signal" | "evidence" | "tech" | "competitor" | "icp";

export type GraphNodeData = {
  kind: GraphNodeType;
  label: string;
  sublabel?: string;
  href?: string;
  signalType?: SignalType;
};

const SIGNAL_TYPE_TO_KEYWORDS: Partial<Record<SignalType, string>> = {
  hiring: "hiring",
  tech_stack: "tech",
  migration: "migration",
  funding: "funding",
  product_launch: "launch",
  leadership_change: "leadership",
  competitor_mention: "competitor",
  champion_move: "champion",
  market_event: "market",
};

function uniqueId(prefix: string, value: string) {
  return `${prefix}:${value.toLowerCase().replace(/\s+/g, "_")}`;
}

function safeUrl(url: string | undefined | null): URL | null {
  if (!url) return null;
  try {
    return new URL(url);
  } catch {
    return null;
  }
}

export function deriveAccountGraph(input: {
  account: AccountRead;
  signals: SignalRead[];
  brief: BriefRead | null;
}): { nodes: Node<GraphNodeData>[]; edges: Edge[] } {
  const { account, signals, brief } = input;
  const nodes: Node<GraphNodeData>[] = [];
  const edges: Edge[] = [];

  const accountId = `acc:${account.id}`;
  // Center node
  nodes.push({
    id: accountId,
    type: "tendril",
    position: { x: 0, y: 0 },
    data: { kind: "account", label: account.name, sublabel: account.domain ?? account.industry ?? undefined },
  });

  // ICP keyword node from account metadata
  const tech = (account.metadata_json as { tech_keywords?: string[] } | undefined)?.tech_keywords;
  if (tech && Array.isArray(tech) && tech.length > 0) {
    const icpId = uniqueId("icp", "tech");
    nodes.push({
      id: icpId,
      type: "tendril",
      position: { x: -260, y: -150 },
      data: { kind: "icp", label: "ICP tech", sublabel: tech.slice(0, 3).join(" · ") },
    });
    edges.push({ id: `${accountId}->${icpId}`, source: accountId, target: icpId, label: "matches_icp" });
  }

  // Signal cluster
  const signalAngles = signals.length > 0 ? (Math.PI * 1.4) / Math.max(signals.length, 1) : 0;
  const baseAngle = -Math.PI * 0.7;
  const radius = 230;
  const techNodes = new Set<string>();

  signals.forEach((signal, idx) => {
    const angle = baseAngle + signalAngles * idx;
    const sx = Math.round(radius * Math.cos(angle));
    const sy = Math.round(radius * Math.sin(angle));
    const signalId = `sig:${signal.id}`;

    nodes.push({
      id: signalId,
      type: "tendril",
      position: { x: sx, y: sy },
      data: {
        kind: "signal",
        label: signal.title,
        sublabel: SIGNAL_TYPE_TO_KEYWORDS[signal.signal_type] ?? signal.signal_type,
        signalType: signal.signal_type,
      },
    });
    edges.push({
      id: `${accountId}->${signalId}`,
      source: accountId,
      target: signalId,
      label: "triggered_by",
    });

    // Evidence host as a leaf
    const url = safeUrl(signal.evidence_url);
    if (url) {
      const evidenceId = uniqueId("ev", `${signalId}:${url.hostname}`);
      if (!nodes.some((n) => n.id === evidenceId)) {
        nodes.push({
          id: evidenceId,
          type: "tendril",
          position: { x: sx + 140, y: sy + 30 },
          data: {
            kind: "evidence",
            label: url.hostname.replace(/^www\./, ""),
            sublabel: url.pathname.length > 24 ? `${url.pathname.slice(0, 24)}…` : url.pathname,
            href: signal.evidence_url,
          },
        });
      }
      edges.push({
        id: `${signalId}->${evidenceId}`,
        source: signalId,
        target: evidenceId,
        label: "evidenced_by",
      });
    }

    // Tech / competitor concept extraction from inference text and metadata
    if (signal.signal_type === "tech_stack" || signal.signal_type === "migration") {
      const candidates = (
        Array.isArray((signal.metadata_json as { keywords?: string[] } | undefined)?.keywords)
          ? ((signal.metadata_json as { keywords?: string[] }).keywords ?? [])
          : []
      )
        .slice(0, 2);
      candidates.forEach((kw, kwIdx) => {
        const techId = uniqueId("tech", kw);
        if (!techNodes.has(techId)) {
          techNodes.add(techId);
          nodes.push({
            id: techId,
            type: "tendril",
            position: { x: sx + 200, y: sy - 60 + kwIdx * 50 },
            data: { kind: "tech", label: kw },
          });
        }
        edges.push({
          id: `${signalId}->${techId}`,
          source: signalId,
          target: techId,
          label: "mentions",
        });
      });
    }
    if (signal.signal_type === "competitor_mention") {
      const candidate =
        (signal.metadata_json as { competitor?: string } | undefined)?.competitor ??
        signal.title.split(":")[0];
      if (candidate) {
        const compId = uniqueId("comp", candidate);
        nodes.push({
          id: compId,
          type: "tendril",
          position: { x: sx + 220, y: sy + 70 },
          data: { kind: "competitor", label: candidate },
        });
        edges.push({
          id: `${signalId}->${compId}`,
          source: signalId,
          target: compId,
          label: "mentions",
        });
      }
    }
  });

  // Brief evidence anchors as additional evidence leaves linked to the account
  if (brief?.key_evidence_json) {
    brief.key_evidence_json.forEach((item, idx) => {
      const url = safeUrl(item.url);
      if (!url) return;
      const evId = uniqueId("ev-brief", `${url.hostname}:${idx}`);
      if (!nodes.some((n) => n.id === evId)) {
        nodes.push({
          id: evId,
          type: "tendril",
          position: { x: 240 + (idx % 2) * 60, y: 220 + Math.floor(idx / 2) * 80 },
          data: {
            kind: "evidence",
            label: url.hostname.replace(/^www\./, ""),
            sublabel: item.source,
            href: url.toString(),
          },
        });
      }
      edges.push({
        id: `${accountId}->${evId}`,
        source: accountId,
        target: evId,
        label: "evidenced_by",
      });
    });
  }

  return { nodes, edges };
}
