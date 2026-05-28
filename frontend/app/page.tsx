import { redirect } from "next/navigation";

export default function RootPage() {
  // Tendril always opens directly into the product. No marketing landing page.
  redirect("/accounts");
}
