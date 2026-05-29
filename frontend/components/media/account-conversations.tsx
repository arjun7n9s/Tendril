"use client";

import { AudioLines, Sparkles } from "lucide-react";
import { useState } from "react";

import { EmptyState } from "@/components/primitives/empty-state";
import { MotionFade } from "@/components/primitives/motion-fade";
import { SectionHeading } from "@/components/primitives/section-heading";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useAccountConversationSignals,
  useAccountMediaSources,
  useStartMediaScan,
} from "@/lib/hooks/use-media-scan";
import { MEDIA_TERMINAL_STAGES } from "@/lib/types";

import { ConversationDrawerProvider } from "./conversation-drawer-context";
import { ConversationSignalCard } from "./conversation-signal-card";
import { MediaScanPanel } from "./media-scan-panel";
import { MediaSourceList } from "./media-source-list";

type AccountConversationsProps = {
  accountId: string;
  latestMediaScanId?: string | null;
  latestMediaScanStatus?: string | null;
};

export function AccountConversations({
  accountId,
  latestMediaScanId,
  latestMediaScanStatus,
}: AccountConversationsProps) {
  const signalsQuery = useAccountConversationSignals(accountId);
  const sourcesQuery = useAccountMediaSources(accountId);
  const startScan = useStartMediaScan(accountId);

  const [panelOpen, setPanelOpen] = useState(false);
  const [explicitScanId, setExplicitScanId] = useState<string | null>(null);

  const activeScanId = explicitScanId ?? latestMediaScanId ?? null;
  const scanRunning =
    startScan.isPending ||
    (latestMediaScanStatus
      ? !MEDIA_TERMINAL_STAGES.has(latestMediaScanStatus as never)
      : false);

  const handleRunScan = async () => {
    try {
      const result = await startScan.mutateAsync({ mode: "live" });
      setExplicitScanId(result.media_scan_id);
      setPanelOpen(true);
    } catch {
      /* toasted by the hook */
    }
  };

  const signals = signalsQuery.data?.items ?? [];
  const sources = sourcesQuery.data ?? [];
  const isLoading = signalsQuery.isLoading || sourcesQuery.isLoading;

  return (
    <ConversationDrawerProvider>
      <section className="flex flex-col gap-3">
        <SectionHeading
          title="Conversations"
          description={
            signals.length > 0
              ? `${signals.length} spoken signal${signals.length === 1 ? "" : "s"} from public sources`
              : "Public spoken sources: podcasts, earnings calls, webinars"
          }
          action={
            <div className="flex items-center gap-2">
              {activeScanId ? (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-[12px]"
                  onClick={() => setPanelOpen(true)}
                >
                  View scan
                </Button>
              ) : null}
              <Button
                variant="signal"
                size="sm"
                className="h-7 px-2.5 text-[12px]"
                loading={scanRunning}
                onClick={handleRunScan}
              >
                <AudioLines className="size-3.5" aria-hidden />
                Run Media Scan
              </Button>
            </div>
          }
        />

        {isLoading ? (
          <div className="flex flex-col gap-3">
            <Skeleton className="h-28 rounded-[var(--radius-card)]" />
            <Skeleton className="h-28 rounded-[var(--radius-card)]" />
          </div>
        ) : signals.length === 0 && sources.length === 0 ? (
          <EmptyState
            illustration={<Sparkles className="size-8 text-graph" />}
            illustrationTone="graph"
            title="No conversations scanned yet"
            body="Run a media scan to discover buying signals buried in podcasts, earnings calls, and webinars — with timestamped, PII-scrubbed evidence."
            action={
              <Button onClick={handleRunScan} loading={scanRunning} variant="signal" size="sm">
                <AudioLines className="size-3.5" aria-hidden />
                Run Media Scan
              </Button>
            }
          />
        ) : (
          <Tabs defaultValue="signals">
            <TabsList>
              <TabsTrigger value="signals">Spoken signals</TabsTrigger>
              <TabsTrigger value="sources">Sources</TabsTrigger>
            </TabsList>
            <TabsContent value="signals">
              {signals.length === 0 ? (
                <p className="py-6 text-center text-[12px] text-fg-muted">
                  No spoken signals extracted yet.
                </p>
              ) : (
                <div className="flex flex-col gap-3">
                  {signals.map((signal, idx) => (
                    <MotionFade key={signal.id} delay={Math.min(idx, 5) * 0.04}>
                      <ConversationSignalCard signal={signal} />
                    </MotionFade>
                  ))}
                </div>
              )}
            </TabsContent>
            <TabsContent value="sources">
              <MediaSourceList sources={sources} />
            </TabsContent>
          </Tabs>
        )}
      </section>

      <MediaScanPanel
        open={panelOpen}
        onOpenChange={(next) => {
          setPanelOpen(next);
          if (!next) {
            signalsQuery.refetch();
            sourcesQuery.refetch();
          }
        }}
        accountId={accountId}
        scanId={activeScanId}
      />
    </ConversationDrawerProvider>
  );
}
