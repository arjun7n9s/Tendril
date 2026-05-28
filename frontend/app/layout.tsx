import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { Toaster } from "sonner";

import { QueryProvider } from "@/lib/providers/query-provider";
import { cn } from "@/lib/utils/cn";

import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin", "latin-ext"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: "swap",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  metadataBase: new URL("http://localhost:3000"),
  title: {
    default: "Tendril",
    template: "%s · Tendril",
  },
  description:
    "Live GTM change intelligence. Tendril scans the public web, turns account changes into evidence-backed signals, and explains why an account matters now.",
  applicationName: "Tendril",
  keywords: [
    "GTM intelligence",
    "sales signals",
    "account intelligence",
    "Bright Data",
    "Cognee",
    "AI/ML API",
  ],
  authors: [{ name: "Tendril" }],
  openGraph: {
    type: "website",
    title: "Tendril",
    description: "Live GTM change intelligence.",
    siteName: "Tendril",
  },
  robots: {
    index: false,
    follow: false,
  },
};

export const viewport: Viewport = {
  themeColor: "#F7F8F6",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={cn(inter.variable, jetbrainsMono.variable, "h-full")}
      suppressHydrationWarning
    >
      <body className="bg-canvas text-fg-primary min-h-full antialiased">
        <QueryProvider>{children}</QueryProvider>
        <Toaster
          position="bottom-right"
          richColors
          closeButton
          duration={3500}
          offset={20}
          toastOptions={{
            classNames: {
              toast:
                "rounded-[8px] border border-[color:var(--color-border-default)] shadow-[var(--shadow-overlay)] data-[type=success]:border-[color:color-mix(in_oklab,var(--color-signal)_30%,transparent)] data-[type=error]:border-[color:color-mix(in_oklab,var(--color-risk)_30%,transparent)]",
              title: "text-[13px] font-semibold",
              description: "text-[12px] text-[color:var(--color-fg-secondary)]",
            },
          }}
        />
      </body>
    </html>
  );
}
