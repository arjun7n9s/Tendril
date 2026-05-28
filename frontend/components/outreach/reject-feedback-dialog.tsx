"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";

type RejectFeedbackDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (feedback: string | undefined) => void;
  isSubmitting?: boolean;
};

export function RejectFeedbackDialog({
  open,
  onOpenChange,
  onSubmit,
  isSubmitting,
}: RejectFeedbackDialogProps) {
  const [feedback, setFeedback] = useState("");

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        onOpenChange(next);
        if (!next) setFeedback("");
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Reject draft</DialogTitle>
          <DialogDescription>
            Optional. Your feedback is logged with the draft so the next regeneration can
            improve.
          </DialogDescription>
        </DialogHeader>
        <Textarea
          placeholder="Why is this draft not ready? (optional)"
          value={feedback}
          onChange={(event) => setFeedback(event.target.value)}
          className="min-h-[120px]"
        />
        <DialogFooter>
          <Button variant="ghost" size="sm" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            size="sm"
            loading={isSubmitting}
            onClick={() => onSubmit(feedback.trim() ? feedback.trim() : undefined)}
          >
            Reject draft
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
