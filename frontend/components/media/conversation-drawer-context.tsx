"use client";

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import type { ConversationSignalRead } from "@/lib/types";

import { ConversationEvidenceDrawer } from "./conversation-evidence-drawer";

type ConversationDrawerContextValue = {
  open(signal: ConversationSignalRead): void;
  close(): void;
};

const ConversationDrawerContext = createContext<ConversationDrawerContextValue | null>(null);

/**
 * Provides a single conversation evidence drawer for the route, openable
 * from any conversation signal card via useConversationDrawer().
 */
export function ConversationDrawerProvider({ children }: { children: ReactNode }) {
  const [signal, setSignal] = useState<ConversationSignalRead | null>(null);

  const open = useCallback((next: ConversationSignalRead) => setSignal(next), []);
  const close = useCallback(() => setSignal(null), []);

  const value = useMemo(() => ({ open, close }), [open, close]);

  return (
    <ConversationDrawerContext.Provider value={value}>
      {children}
      <ConversationEvidenceDrawer
        signal={signal}
        onOpenChange={(next) => {
          if (!next) close();
        }}
      />
    </ConversationDrawerContext.Provider>
  );
}

export function useConversationDrawer(): ConversationDrawerContextValue {
  const ctx = useContext(ConversationDrawerContext);
  if (!ctx) {
    throw new Error("useConversationDrawer must be used inside a ConversationDrawerProvider");
  }
  return ctx;
}
