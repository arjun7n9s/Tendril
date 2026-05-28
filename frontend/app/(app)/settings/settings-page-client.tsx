"use client";

import { CheckCircle2, CircleDashed, ExternalLink } from "lucide-react";

import { TopCommandBar } from "@/components/app-shell/top-command-bar";
import { Skeleton } from "@/components/ui/skeleton";
import { useHealth } from "@/lib/hooks/use-health";
import type { HealthResponse, IntegrationFlag } from "@/lib/types";
import { cn } from "@/lib/utils/cn";

type Row = {
  key: keyof Pick<
    HealthResponse,
    | "bright_data_rest"
    | "bright_data_browser"
    | "bright_data_mcp"
    | "aiml_api"
    | "cognee"
    | "triggerware"
    | "speechmatics"
  >;
  name: string;
  description: string;
  docs?: string;
};

const ROWS: Row[] = [
  {
    key: "bright_data_rest",
    name: "Bright Data REST",
    description: "SERP API + Web Unlocker zones for live web acquisition.",
    docs: "https://docs.brightdata.com/scraping-automation/introduction",
  },
  {
    key: "bright_data_browser",
    name: "Bright Data Browser API",
    description: "Scraping Browser for JS-heavy pages.",
    docs: "https://docs.brightdata.com/scraping-automation/scraping-browser/introduction",
  },
  {
    key: "bright_data_mcp",
    name: "Bright Data MCP",
    description: "Optional MCP server for agentic search and structured extraction.",
    docs: "https://docs.brightdata.com/ai/mcp-server/tools",
  },
  {
    key: "aiml_api",
    name: "AI/ML API",
    description: "OpenAI-compatible model gateway for extraction, briefing, and drafts.",
    docs: "https://docs.aimlapi.com",
  },
  {
    key: "cognee",
    name: "Cognee",
    description: "Persistent graph memory for accounts, champions, and signals.",
    docs: "https://docs.cognee.ai/core-concepts/main-operations/remember",
  },
  {
    key: "triggerware",
    name: "Triggerware",
    description: "Optional automation layer for scheduled scans and notifications.",
  },
  {
    key: "speechmatics",
    name: "Speechmatics",
    description: "Optional voice-note transcription pipeline.",
  },
];

export function SettingsPageClient() {
  const { data, isLoading } = useHealth();

  return (
    <>
      <TopCommandBar
        title="Settings"
        subtitle="Integration status, environment, and credits"
      />
      <div className="flex flex-col gap-5 px-6 py-5">
        <section className="flex flex-col gap-3">
          <header className="flex items-baseline justify-between gap-3 border-b border-[color:var(--color-border-default)] pb-2">
            <h2 className="text-[12px] font-semibold tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
              Environment
            </h2>
            <span className="text-[11px] tabular-nums text-[color:var(--color-fg-muted)]">
              {data?.app_env ?? "—"}
            </span>
          </header>
          {isLoading ? (
            <Skeleton className="h-12 rounded-[var(--radius-card)]" />
          ) : (
            <ul className="grid grid-cols-1 gap-2 md:grid-cols-3">
              <KeyValue label="App env" value={data?.app_env ?? "—"} />
              <KeyValue
                label="Mode"
                value={data?.mock_mode ? "Mock" : "Live"}
                accent={data?.mock_mode ? "neutral" : "cobalt"}
              />
              <KeyValue
                label="Database"
                value={data?.database === "ok" ? "Healthy" : "Error"}
                accent={data?.database === "ok" ? "signal" : "risk"}
              />
            </ul>
          )}
        </section>

        <section className="flex flex-col gap-3">
          <header className="flex items-baseline justify-between gap-3 border-b border-[color:var(--color-border-default)] pb-2">
            <h2 className="text-[12px] font-semibold tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
              Integrations
            </h2>
          </header>
          {isLoading ? (
            <div className="flex flex-col gap-2">
              {Array.from({ length: 7 }).map((_, idx) => (
                <Skeleton key={idx} className="h-14 rounded-[var(--radius-card)]" />
              ))}
            </div>
          ) : (
            <ul className="flex flex-col overflow-hidden rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)]">
              {ROWS.map((row) => {
                const flag: IntegrationFlag = data?.[row.key] ?? "not_configured";
                const configured = flag === "configured";
                return (
                  <li
                    key={row.key}
                    className="flex items-start justify-between gap-4 border-b border-[color:var(--color-border-default)] px-4 py-3 last:border-b-0"
                  >
                    <div className="flex flex-col gap-0.5">
                      <span className="inline-flex items-center gap-2 text-[14px] font-semibold text-[color:var(--color-fg-primary)]">
                        {row.name}
                        {row.docs ? (
                          <a
                            href={row.docs}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[color:var(--color-fg-muted)] hover:text-[color:var(--color-fg-primary)]"
                            aria-label={`${row.name} docs`}
                          >
                            <ExternalLink className="size-3" aria-hidden />
                          </a>
                        ) : null}
                      </span>
                      <span className="text-[12px] text-[color:var(--color-fg-secondary)]">
                        {row.description}
                      </span>
                    </div>
                    <span
                      className={cn(
                        "inline-flex shrink-0 items-center gap-1 rounded-[var(--radius-chip)] border px-1.5 py-0.5 text-[11px] font-medium tracking-[0.04em] uppercase",
                        configured
                          ? "border-[color:color-mix(in_oklab,var(--color-signal)_30%,transparent)] bg-[color:var(--color-signal-soft)] text-[color:var(--color-signal)]"
                          : "border-[color:var(--color-border-default)] bg-[color:var(--color-raised)] text-[color:var(--color-fg-muted)]",
                      )}
                    >
                      {configured ? (
                        <CheckCircle2 className="size-3" aria-hidden />
                      ) : (
                        <CircleDashed className="size-3" aria-hidden />
                      )}
                      {configured ? "Configured" : "Not configured"}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        <section className="rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] p-4">
          <h2 className="text-[12px] font-semibold tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
            About
          </h2>
          <p className="mt-2 text-[13px] leading-relaxed text-[color:var(--color-fg-primary)]">
            Tendril is built on Next.js, FastAPI, Bright Data, AI/ML API, and Cognee. Designed
            and built for the Bright Data Web Data Unlocked Hackathon.
          </p>
          <p className="mt-2 text-[12px] text-[color:var(--color-fg-muted)]">
            Live web access requires Bright Data credentials. Mock mode runs offline.
          </p>
        </section>
      </div>
    </>
  );
}

function KeyValue({
  label,
  value,
  accent = "neutral",
}: {
  label: string;
  value: string;
  accent?: "neutral" | "signal" | "cobalt" | "risk";
}) {
  const ACCENT = {
    neutral: "text-[color:var(--color-fg-primary)]",
    signal: "text-[color:var(--color-signal)]",
    cobalt: "text-[color:var(--color-cobalt)]",
    risk: "text-[color:var(--color-risk)]",
  } as const;
  return (
    <li className="flex flex-col gap-1 rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] p-3 shadow-[var(--shadow-flat)]">
      <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
        {label}
      </span>
      <span className={cn("text-[15px] font-semibold", ACCENT[accent])}>{value}</span>
    </li>
  );
}
