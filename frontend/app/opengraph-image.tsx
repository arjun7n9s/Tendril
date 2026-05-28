import { ImageResponse } from "next/og";

export const runtime = "edge";

export const alt = "Tendril — Live GTM change intelligence";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/**
 * Programmatically rendered Open Graph image. Drawn from the same
 * tokens as the rest of the app so the social card matches what
 * users see inside the product.
 */
export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "96px",
          background: "#F7F8F6",
          color: "#171A1C",
          fontFamily: "Inter, system-ui, sans-serif",
          letterSpacing: "-0.01em",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <svg width="56" height="56" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="7" fill="#171A1C" />
            <g
              stroke="#FFFFFF"
              strokeWidth={2.4}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M9 22 C 9 14, 14 10, 20 10 S 26 14, 24 19 C 22.4 23, 17 23, 16 19 C 15.2 15.6, 18.5 14, 20 16" />
              <circle cx="20" cy="16" r="1.6" fill="#FFFFFF" stroke="none" />
            </g>
          </svg>
          <span style={{ fontSize: 44, fontWeight: 600 }}>Tendril</span>
        </div>
        <div
          style={{
            marginTop: 56,
            fontSize: 84,
            lineHeight: 1.05,
            fontWeight: 600,
            maxWidth: 920,
          }}
        >
          Live GTM change intelligence.
        </div>
        <div
          style={{
            marginTop: 32,
            fontSize: 28,
            color: "#5D656B",
            maxWidth: 880,
            lineHeight: 1.35,
          }}
        >
          Evidence-backed signals from the public web. Powered by Bright Data, AI/ML API, and a
          memory graph.
        </div>
        <div
          style={{
            position: "absolute",
            bottom: 64,
            right: 96,
            display: "flex",
            alignItems: "center",
            gap: 12,
            fontSize: 18,
            color: "#5D656B",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
          }}
        >
          <span style={{ width: 8, height: 8, background: "#0F9F6E", borderRadius: 999 }} />
          tendril
        </div>
      </div>
    ),
    {
      ...size,
    },
  );
}
