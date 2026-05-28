"use client";

import { ExternalLink, RefreshCw } from "lucide-react";

import { SectionHeading } from "@/components/primitives/section-heading";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { COPY } from "@/lib/copy";
import type { BriefRead } from "@/lib/types";

type AccountBriefPanelProps = {
  brief: BriefRead | null;
  isLoading?: boolean;
  isRegenerating?: boolean;
  onRegenerate?: () => void;
};

export function AccountBriefPanel({
  brief,
  isLoading,
  isRegenerating,
  onRegenerate,
}: AccountBriefPanelProps) {
  if (isLoading) {
    return (
      <section className="flex flex-col gap-3 rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] p-4 shadow-[var(--shadow-flat)]">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-3/4" />
        <Skeleton className="h-3 w-2/3" />
      </section>
    );
  }

  if (!brief) {
    return (
      <section className="flex flex-col gap-2 rounded-[var(--radius-card)] border border-dashed border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] p-4">
        <h3 className="text-[13px] font-semibold tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
          Account brief
        </h3>
        <p className="text-[13px] text-[color:var(--color-fg-muted)]">
          The first scan generates an evidence-backed account brief. Run a live scan to populate
          this panel.
        </p>
      </section>
    );
  }

  return (
    <section className="flex flex-col gap-4 rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] p-4 shadow-[var(--shadow-flat)]">
      <SectionHeading
        title="Account brief"
        description={brief.title}
        action={
          onRegenerate ? (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-[12px]"
              onClick={onRegenerate}
              loading={isRegenerating}
            >
              {!isRegenerating ? <RefreshCw className="size-3" aria-hidden /> : null}
              Regenerate
            </Button>
          ) : null
        }
      />

      {brief.executive_summary ? (
        <BriefSection label={COPY.brief.executiveSummary} text={brief.executive_summary} />
      ) : null}

      {brief.why_now ? (
        <BriefSection
          label={COPY.brief.whyNow}
          text={brief.why_now}
          accent="evidence"
        />
      ) : null}

      {brief.key_evidence_json && brief.key_evidence_json.length > 0 ? (
        <div className="flex flex-col gap-1.5">
          <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
            {COPY.brief.keyEvidence}
          </span>
          <ul className="flex flex-col gap-1">
            {brief.key_evidence_json.map((item, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-[13px] leading-snug text-[color:var(--color-fg-primary)]"
              >
                <span className="mt-1 size-1.5 shrink-0 rounded-full bg-[color:var(--color-fg-muted)]" />
                <span className="flex-1">
                  {item.text}
                  {item.url ? (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="ml-1 inline-flex items-center gap-0.5 text-[12px] text-[color:var(--color-fg-secondary)] hover:text-[color:var(--color-fg-primary)]"
                    >
                      <ExternalLink className="size-3" aria-hidden />
                      {item.source ?? "source"}
                    </a>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {brief.risks_json && brief.risks_json.length > 0 ? (
        <BriefList label={COPY.brief.risks} items={brief.risks_json} accent="risk" />
      ) : null}

      {brief.recommended_next_steps_json && brief.recommended_next_steps_json.length > 0 ? (
        <BriefList
          label={COPY.brief.nextSteps}
          items={brief.recommended_next_steps_json}
          accent="signal"
        />
      ) : null}
    </section>
  );
}

function BriefSection({
  label,
  text,
  accent,
}: {
  label: string;
  text: string;
  accent?: "evidence";
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
        {label}
      </span>
      <p
        className={
          accent === "evidence"
            ? "rounded-[var(--radius-chip)] border-l-2 border-[color:var(--color-evidence)] bg-[color:var(--color-evidence-soft)]/40 px-3 py-2 text-[13px] leading-relaxed text-[color:var(--color-fg-primary)]"
            : "text-[13px] leading-relaxed text-[color:var(--color-fg-primary)]"
        }
      >
        {text}
      </p>
    </div>
  );
}

function BriefList({
  label,
  items,
  accent,
}: {
  label: string;
  items: string[];
  accent: "risk" | "signal";
}) {
  const dotClass =
    accent === "risk"
      ? "bg-[color:var(--color-risk)]"
      : "bg-[color:var(--color-signal)]";
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-[11px] tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
        {label}
      </span>
      <ul className="flex flex-col gap-1">
        {items.map((item, idx) => (
          <li
            key={idx}
            className="flex items-start gap-2 text-[13px] leading-snug text-[color:var(--color-fg-primary)]"
          >
            <span className={`mt-1 size-1.5 shrink-0 rounded-full ${dotClass}`} />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
