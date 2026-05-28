/**
 * Centralized UI copy.
 *
 * Source: kiro/kiro-frontend-architecture.md §23 + kiro/kiro-frontend-assets-plan.md §11.
 * Edit here, never inline. Lets us audit tone in one pass.
 */
export const COPY = {
  product: {
    name: "Tendril",
    tagline: "Live GTM change intelligence",
  },
  scan: {
    primary: "Run Live Scan",
    primaryRunning: "Scan in progress",
    completionToast: "New account intelligence is ready",
    failureToast: "Scan failed. Check the event log for details.",
    queuedToast: "Scan queued",
  },
  badges: {
    salesReady: "Sales-ready",
    nearMiss: "Needs one more signal",
    target: "Target",
    customer: "Customer",
    formerCustomer: "Former customer",
    competitor: "Competitor",
    ignored: "Ignored",
  },
  evidence: {
    button: "View evidence",
    drawerTitle: "Evidence",
    openOriginal: "Open original source",
    fetchedVia: "Fetched via",
  },
  brief: {
    whyNow: "Why now",
    executiveSummary: "Executive summary",
    keyEvidence: "Key evidence",
    risks: "Risks and uncertainty",
    nextSteps: "Recommended next steps",
    regenerate: "Regenerate brief",
    regenerated: "Brief regenerated",
  },
  outreach: {
    guardrailHeading: "Human approval required",
    approvedToast: "Draft approved and logged",
    rejectedToast: "Draft rejected",
    editedToast: "Draft updated",
    queueEmpty: "No pending drafts. Run a scan on a target account to generate one.",
  },
  imports: {
    title: "Import seed data",
    subtitle:
      "Drop a CRM CSV with target accounts, prior champions, and best-customer examples. We will normalize the rows, store them, and prime the dashboard.",
    success: "Seed imported",
  },
  empty: {
    accountsTitle: "No accounts yet",
    accountsBody: "Import a seed CSV or load the demo seed to get started.",
    signalsTitle: "No signals yet",
    signalsBody: "Run a scan to surface evidence-backed account changes.",
  },
  demo: {
    primedToast: "Demo seed loaded",
    primedDescription: "Five seeded accounts and prior champions are ready.",
  },
};

export type CopyKey = typeof COPY;
