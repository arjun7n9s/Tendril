import { Suspense } from "react";

import { SignalsPageClient } from "./signals-page-client";

export const metadata = {
  title: "Signal feed",
};

export default function SignalsPage() {
  return (
    <Suspense fallback={null}>
      <SignalsPageClient />
    </Suspense>
  );
}
