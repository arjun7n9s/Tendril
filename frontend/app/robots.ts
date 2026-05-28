import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  // Tendril is a hackathon demo build; we never want public crawlers
  // indexing the workspace dashboard.
  return {
    rules: [{ userAgent: "*", disallow: "/" }],
  };
}
