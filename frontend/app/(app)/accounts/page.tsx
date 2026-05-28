import { Suspense } from "react";

import { AccountsPageClient } from "./accounts-page-client";

export const metadata = {
  title: "Accounts",
};

export default function AccountsPage() {
  return (
    <Suspense fallback={null}>
      <AccountsPageClient />
    </Suspense>
  );
}
