import type { Metadata } from "next";

import { TodayPageClient } from "./today-page-client";

export const metadata: Metadata = {
  title: "Today",
};

export default function TodayPage() {
  return <TodayPageClient />;
}
