"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useState } from "react";

import { AccountHeader } from "@/components/accounts/account-header";
import { AccountScoreStrip } from "@/components/accounts/account-score-strip";
import { TopCommandBar } from "@/components/app-shell/top-command-bar";
import { AccountBriefPanel } from "@/components/briefs/account-brief-panel";
import { EvidenceDrawerProvider } from "@/components/evidence/evidence-drawer-context";
import {
  EmptySignalsIllustration,
  ErrorStateIllustration,
} from "@/components/illustrations";
import { AccountConversations } from "@/components/media/account-conversations";
import { AccountOutreachPreview } from "@/components/outreach/account-outreach-preview";
import { EmptyState } from "@/components/primitives/empty-state";
import { SectionHeading } from "@/components/primitives/section-heading";
import { LiveScanPanel } from "@/components/scans/live-scan-panel";
import { SignalCard } from "@/components/signals/signal-card";
import { SignalTimeline } from "@/components/signals/signal-timeline";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MotionFade } from "@/components/primitives/motion-fade";
import { useAccountDetail } from "@/lib/hooks/use-accounts";
import { useStartScan } from "@/lib/hooks/use-scan";
import { NON_TERMINAL_SCAN_STATUSES } from "@/lib/types";

// React Flow is heavy and only renders inside the Graph tab. Lazy-load
// it so the bundle for the Signals/Timeline tabs stays light.
const AccountKnowledgeGraph = dynamic(
  () =>
    import("@/components/graph/account-knowledge-graph").then(
      (mod) => mod.AccountKnowledgeGraph,
    ),
  {
    ssr: false,
    loading: () => <Skeleton className="h-[540px] rounded-[var(--radius-card)]" />,
  },
);

type Props = { accountId: string };

export function AccountDetailClient({ accountId }: Props) {
  const detail = useAccountDetail(accountId);
  const startScan = useStartScan(accountId);

  const [panelOpen, setPanelOpen] = useState(false);
  // Tracks scan ids the user explicitly opened (just-started or "View
  // scan"). When null we fall back to the latest_scan from detail data,
  // so non-terminal background scans are picked up automatically
  // without an effect-based sync.
  const [explicitScanId, setExplicitScanId] = useState<string | null>(null);

  const latestScan = detail.data?.latest_scan ?? null;
  const activeScanId =
    explicitScanId ??
    (latestScan && NON_TERMINAL_SCAN_STATUSES.has(latestScan.status) ? latestScan.id : null) ??
    latestScan?.id ??
    null;

  const handleRunScan = async () => {
    try {
      const result = await startScan.mutateAsync({ mode: "live" });
      setExplicitScanId(result.scan_id);
      setPanelOpen(true);
    } catch {
      /* error already toasted by the hook */
    }
  };

  if (detail.isLoading) {
    return (
      <>
        <TopCommandBar title="Loading…" />
        <div className="flex flex-col gap-5 px-6 py-5">
          <Skeleton className="h-32 rounded-[var(--radius-card)]" />
          <Skeleton className="h-48 rounded-[var(--radius-card)]" />
        </div>
      </>
    );
  }

  if (detail.isError || !detail.data) {
    return (
      <>
        <TopCommandBar title="Account" />
        <div className="px-6 py-10">
          <EmptyState
            illustration={<ErrorStateIllustration />}
            illustrationTone="risk"
            title="Account not found"
            body="The requested account does not exist or the backend is unreachable."
            action={
              <Button asChild size="sm">
                <Link href="/accounts">Back to accounts</Link>
              </Button>
            }
          />
        </div>
      </>
    );
  }

  const { account, latest_scan, latest_score, latest_score_snapshot, latest_brief, recent_signals } = detail.data;
  const scanRunning =
    startScan.isPending ||
    (latest_scan ? NON_TERMINAL_SCAN_STATUSES.has(latest_scan.status) : false);

  return (
    <EvidenceDrawerProvider>
      <TopCommandBar
        title={account.name}
        subtitle={account.domain ?? "No domain on file"}
        primaryAction={
          <Button asChild variant="ghost" size="sm">
            <Link href="/accounts">All accounts</Link>
          </Button>
        }
      />
      <div className="flex flex-col gap-5">
        <AccountHeader
          account={account}
          lastScannedAt={latest_scan?.completed_at}
          onRunScan={handleRunScan}
          isScanRunning={scanRunning}
        />

        <div className="flex flex-col gap-5 px-6 pb-8">
          <AccountScoreStrip score={latest_score} snapshot={latest_score_snapshot} brief={latest_brief} />

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
            <section className="flex flex-col gap-3">
              <SectionHeading
                title="Intelligence"
                description={
                  recent_signals.length > 0
                    ? `${recent_signals.length} from latest scan`
                    : "No signals yet"
                }
                action={
                  latest_scan ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-[12px]"
                      onClick={() => {
                        setExplicitScanId(latest_scan.id);
                        setPanelOpen(true);
                      }}
                    >
                      View scan
                    </Button>
                  ) : null
                }
              />

              {recent_signals.length === 0 ? (
                <EmptyState
                  illustration={<EmptySignalsIllustration />}
                  illustrationTone="cobalt"
                  title="No signals yet"
                  body="Run a live scan to discover hiring, migration, and champion changes for this account."
                  action={
                    <Button onClick={handleRunScan} loading={scanRunning} variant="signal" size="sm">
                      Run Live Scan
                    </Button>
                  }
                />
              ) : (
                <Tabs defaultValue="signals">
                  <TabsList>
                    <TabsTrigger value="signals">Signals</TabsTrigger>
                    <TabsTrigger value="timeline">Timeline</TabsTrigger>
                    <TabsTrigger value="graph">Graph</TabsTrigger>
                  </TabsList>
                  <TabsContent value="signals">
                    <div className="flex flex-col gap-3">
                      {recent_signals.map((signal, idx) => (
                        <MotionFade
                          key={signal.id}
                          delay={Math.min(idx, 5) * 0.04}
                        >
                          <SignalCard signal={signal} />
                        </MotionFade>
                      ))}
                    </div>
                  </TabsContent>
                  <TabsContent value="timeline">
                    <SignalTimeline signals={recent_signals} />
                  </TabsContent>
                  <TabsContent value="graph">
                    <AccountKnowledgeGraph
                      account={account}
                      signals={recent_signals}
                      brief={latest_brief}
                    />
                    <p className="mt-2 text-[11px] text-[color:var(--color-fg-muted)]">
                      Derived locally from the latest scan&rsquo;s signals, evidence URLs, and
                      brief. Cognee-backed relationships will replace this view once the graph
                      endpoint ships.
                    </p>
                  </TabsContent>
                </Tabs>
              )}
            </section>

            <aside className="flex flex-col gap-4">
              <AccountBriefPanel brief={latest_brief} />
              <AccountOutreachPreview accountId={accountId} />
            </aside>
          </div>

          <AccountConversations accountId={accountId} />
        </div>
      </div>

      <LiveScanPanel
        open={panelOpen}
        onOpenChange={(next) => {
          setPanelOpen(next);
          if (!next) {
            // Re-fetch the account detail when the user closes the
            // panel so the score strip and signals reflect the run.
            detail.refetch();
          }
        }}
        accountId={accountId}
        scanId={activeScanId}
      />
    </EvidenceDrawerProvider>
  );
}
