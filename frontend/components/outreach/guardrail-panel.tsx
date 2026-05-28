"use client";

import { CheckCircle2, ShieldCheck, TriangleAlert } from "lucide-react";

import { COPY } from "@/lib/copy";
import type { OutreachRead } from "@/lib/types";

const STANDARD_CHECKS = [
  "Uses public evidence",
  "Avoids creepy phrasing",
  "No unsupported claims",
  "Human approval required",
];

export function GuardrailPanel({ draft }: { draft: OutreachRead }) {
  const notes = (draft.guardrail_notes_json ?? []) as Array<
    string | { text?: string; warning?: boolean }
  >;
  const warnings = notes.filter(
    (note) => typeof note === "object" && note?.warning,
  ) as Array<{ text?: string }>;

  return (
    <section className="flex flex-col gap-4 rounded-[var(--radius-card)] border border-[color:var(--color-border-default)] bg-[color:var(--color-surface)] p-4 shadow-[var(--shadow-flat)]">
      <header className="flex items-center gap-2">
        <ShieldCheck
          className="size-4 text-[color:var(--color-signal)]"
          aria-hidden
        />
        <h3 className="text-[13px] font-semibold tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
          {COPY.outreach.guardrailHeading}
        </h3>
      </header>

      <ul className="flex flex-col gap-1.5">
        {STANDARD_CHECKS.map((check) => (
          <li
            key={check}
            className="flex items-center gap-2 text-[13px] text-[color:var(--color-fg-primary)]"
          >
            <CheckCircle2
              className="size-3.5 text-[color:var(--color-signal)]"
              aria-hidden
            />
            {check}
          </li>
        ))}
      </ul>

      {warnings.length > 0 ? (
        <div className="flex flex-col gap-1.5 rounded-[var(--radius-chip)] border border-[color:color-mix(in_oklab,var(--color-evidence)_30%,transparent)] bg-[color:var(--color-evidence-soft)] p-2.5">
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold tracking-[0.04em] uppercase text-[color:var(--color-evidence)]">
            <TriangleAlert className="size-3" aria-hidden />
            Review before approving
          </span>
          {warnings.map((warning, idx) => (
            <p key={idx} className="text-[12px] text-[color:var(--color-fg-primary)]">
              {warning.text ?? JSON.stringify(warning)}
            </p>
          ))}
        </div>
      ) : null}

      {notes.length > 0 && warnings.length === 0 ? (
        <details className="text-[12px] text-[color:var(--color-fg-secondary)]">
          <summary className="cursor-pointer font-medium text-[color:var(--color-fg-primary)]">
            {notes.length} guardrail note{notes.length === 1 ? "" : "s"}
          </summary>
          <ul className="mt-1 list-inside list-disc space-y-0.5">
            {notes.map((note, idx) => (
              <li key={idx}>{typeof note === "string" ? note : (note.text ?? JSON.stringify(note))}</li>
            ))}
          </ul>
        </details>
      ) : null}

      <footer className="border-t border-[color:var(--color-border-default)] pt-3 text-[12px] text-[color:var(--color-fg-muted)]">
        Approval is logged but no email is sent. CRM writeback is out of scope for the demo
        build.
      </footer>
    </section>
  );
}
