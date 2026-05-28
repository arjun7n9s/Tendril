import { Megaphone } from "lucide-react";

import { TopCommandBar } from "@/components/app-shell/top-command-bar";
import { EmptyState } from "@/components/primitives/empty-state";

export const metadata = {
  title: "Outreach",
};

export default function OutreachPage() {
  return (
    <>
      <TopCommandBar
        title="Outreach review"
        subtitle="Human approval before any draft leaves Tendril"
      />
      <div className="px-6 py-8">
        <EmptyState
          icon={Megaphone}
          title="Outreach cockpit ships in Phase 2"
          body="Approved drafts will appear here with their guardrail checklist and the evidence they cite. For now, run a scan and inspect the brief on the account detail page."
        />
      </div>
    </>
  );
}
