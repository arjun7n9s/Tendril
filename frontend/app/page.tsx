import { redirect } from "next/navigation";

export default function RootPage() {
  // Tendril always opens directly into the product — into the opinionated
  // "Today" queue, not a marketing landing page.
  redirect("/today");
}
