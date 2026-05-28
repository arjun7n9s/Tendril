"use client";

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import type { EvidenceRead, SignalRead } from "@/lib/types";

import { EvidenceDrawer } from "./evidence-drawer";

type DrawerSubject =
  | { kind: "signal"; signal: SignalRead; scanId?: string | null }
  | { kind: "evidence"; evidence: EvidenceRead };

type EvidenceDrawerContextValue = {
  open(subject: DrawerSubject): void;
  close(): void;
};

const EvidenceDrawerContext = createContext<EvidenceDrawerContextValue | null>(null);

/**
 * Provides a single Evidence Drawer instance for the route, openable
 * from any descendant via useEvidenceDrawer().
 *
 * Centralizing the drawer here means SignalCards, BriefPanels, and
 * the ScanSourceStream can all delegate to the same component
 * without each sprouting their own portal.
 */
export function EvidenceDrawerProvider({ children }: { children: ReactNode }) {
  const [subject, setSubject] = useState<DrawerSubject | null>(null);

  const open = useCallback((next: DrawerSubject) => setSubject(next), []);
  const close = useCallback(() => setSubject(null), []);

  const value = useMemo(() => ({ open, close }), [open, close]);

  return (
    <EvidenceDrawerContext.Provider value={value}>
      {children}
      <EvidenceDrawer
        subject={subject}
        onOpenChange={(next) => {
          if (!next) close();
        }}
      />
    </EvidenceDrawerContext.Provider>
  );
}

export function useEvidenceDrawer(): EvidenceDrawerContextValue {
  const ctx = useContext(EvidenceDrawerContext);
  if (!ctx) {
    throw new Error("useEvidenceDrawer must be used inside an EvidenceDrawerProvider");
  }
  return ctx;
}
