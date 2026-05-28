import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Tendril",
    short_name: "Tendril",
    description: "Live GTM change intelligence.",
    start_url: "/accounts",
    display: "standalone",
    background_color: "#F7F8F6",
    theme_color: "#F7F8F6",
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml",
      },
    ],
  };
}
