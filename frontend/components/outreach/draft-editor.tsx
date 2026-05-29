"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Check, Save, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { StatusChip } from "@/components/primitives/status-chip";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useApproveDraft, useEditDraft, useRejectDraft } from "@/lib/hooks/use-outreach";
import { EMPHASIS } from "@/lib/motion";
import type { OutreachRead, OutreachTone } from "@/lib/types";
import { cn } from "@/lib/utils/cn";

import { RejectFeedbackDialog } from "./reject-feedback-dialog";
import { ToneToggle } from "./tone-toggle";

type DraftEditorProps = {
  draft: OutreachRead;
};

/**
 * The editor stores its own copies of subject/body/tone so the user
 * can iterate without round-tripping through the server. The parent
 * remounts this component whenever the active draft id changes (via
 * `key={draft.id}`), which gives us a clean reset without an effect-
 * based sync that React 19 disallows.
 */
export function DraftEditor({ draft }: DraftEditorProps) {
  const approve = useApproveDraft(draft.id);
  const reject = useRejectDraft(draft.id);
  const edit = useEditDraft(draft.id);

  const [subject, setSubject] = useState(draft.subject);
  const [body, setBody] = useState(draft.body);
  const [tone, setTone] = useState<OutreachTone>(draft.tone);
  const [rejectOpen, setRejectOpen] = useState(false);

  const isDirty = subject !== draft.subject || body !== draft.body || tone !== draft.tone;

  const isTerminal = draft.status === "approved" || draft.status === "rejected";

  // Pulse the status chip when the draft transitions to a terminal
  // state. Subtle, single-shot, respects reduced motion.
  const reduce = useReducedMotion();
  const previousStatus = useRef(draft.status);
  const [pulseKey, setPulseKey] = useState(0);
  useEffect(() => {
    if (previousStatus.current !== draft.status && isTerminal) {
      setPulseKey((n) => n + 1);
    }
    previousStatus.current = draft.status;
  }, [draft.status, isTerminal]);

  return (
    <div className="flex h-full flex-col gap-4">
      <header className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
        <div className="flex items-center gap-2">
          <motion.span
            key={pulseKey}
            initial={false}
            animate={
              reduce || pulseKey === 0
                ? undefined
                : { scale: [1, 1.08, 1] }
            }
            transition={EMPHASIS}
            className="inline-flex"
          >
            <StatusChip kind="outreach" value={draft.status} />
          </motion.span>
          <span className="text-[12px] tracking-[0.04em] text-[color:var(--color-fg-muted)] uppercase">
            Draft #{draft.id.slice(-6)}
          </span>
        </div>
        <ToneToggle
          value={tone}
          onChange={(next) => {
            setTone(next);
          }}
          disabled={isTerminal}
        />
      </header>

      <div className="flex flex-col gap-1.5">
        <label
          className="text-[11px] font-semibold tracking-[0.04em] text-[color:var(--color-fg-secondary)] uppercase"
          htmlFor="draft-subject"
        >
          Subject
        </label>
        <Input
          id="draft-subject"
          value={subject}
          onChange={(event) => setSubject(event.target.value)}
          disabled={isTerminal}
        />
      </div>

      <div className={cn("flex flex-col gap-1.5", "flex-1")}>
        <label
          className="text-[11px] font-semibold tracking-[0.04em] text-[color:var(--color-fg-secondary)] uppercase"
          htmlFor="draft-body"
        >
          Body
        </label>
        <Textarea
          id="draft-body"
          value={body}
          onChange={(event) => setBody(event.target.value)}
          disabled={isTerminal}
          className="min-h-[280px]"
        />
      </div>

      <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-[color:var(--color-border-default)] pt-3">
        <div className="flex items-center gap-2">
          {isDirty ? (
            <Button
              variant="secondary"
              size="sm"
              loading={edit.isPending}
              onClick={() =>
                edit.mutate({
                  subject: subject !== draft.subject ? subject : undefined,
                  body: body !== draft.body ? body : undefined,
                  tone: tone !== draft.tone ? tone : undefined,
                })
              }
            >
              <Save className="size-3.5" aria-hidden />
              Save edits
            </Button>
          ) : null}
          {isDirty ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSubject(draft.subject);
                setBody(draft.body);
                setTone(draft.tone);
              }}
            >
              Discard
            </Button>
          ) : null}
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setRejectOpen(true)}
            disabled={isTerminal}
          >
            <X className="size-3.5" aria-hidden />
            Reject
          </Button>
          <Button
            variant="signal"
            size="sm"
            loading={approve.isPending}
            disabled={isTerminal || isDirty}
            onClick={() => approve.mutate()}
            title={isDirty ? "Save edits before approving" : undefined}
          >
            <Check className="size-3.5" aria-hidden />
            Approve
          </Button>
        </div>
      </footer>

      <RejectFeedbackDialog
        open={rejectOpen}
        onOpenChange={setRejectOpen}
        isSubmitting={reject.isPending}
        onSubmit={(feedback) => {
          reject.mutate(feedback, {
            onSuccess: () => setRejectOpen(false),
          });
        }}
      />
    </div>
  );
}
