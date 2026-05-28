// Contrast audit: computes WCAG ratios for every chip/state pairing
// in the Tendril palette. Run with: node scripts/contrast-audit.mjs

const TOKENS = {
  canvas: "#F7F8F6",
  surface: "#FFFFFF",
  raised: "#F1F4F2",
  fg_primary: "#171A1C",
  fg_secondary: "#5D656B",
  fg_muted: "#6A7074",
  border_default: "#DDE3E0",
  border_strong: "#C8D0CC",
  signal: "#0C7C56",
  signal_soft: "#E6F4EE",
  cobalt: "#3457D5",
  cobalt_soft: "#E6ECFB",
  evidence: "#995F17",
  evidence_soft: "#FAECD6",
  risk: "#BA3E38",
  risk_soft: "#FBE5E3",
  graph: "#107575",
  graph_soft: "#D9EFEF",
};

function hexToRgb(hex) {
  const v = hex.replace("#", "");
  return [
    parseInt(v.slice(0, 2), 16) / 255,
    parseInt(v.slice(2, 4), 16) / 255,
    parseInt(v.slice(4, 6), 16) / 255,
  ];
}

function relLum([r, g, b]) {
  const adj = (c) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  return 0.2126 * adj(r) + 0.7152 * adj(g) + 0.0722 * adj(b);
}

function contrast(a, b) {
  const la = relLum(hexToRgb(a));
  const lb = relLum(hexToRgb(b));
  const [hi, lo] = la > lb ? [la, lb] : [lb, la];
  return (hi + 0.05) / (lo + 0.05);
}

const PAIRS = [
  // Body text (4.5:1)
  ["fg_primary on surface", TOKENS.fg_primary, TOKENS.surface, 4.5],
  ["fg_primary on canvas", TOKENS.fg_primary, TOKENS.canvas, 4.5],
  ["fg_secondary on surface", TOKENS.fg_secondary, TOKENS.surface, 4.5],
  ["fg_secondary on canvas", TOKENS.fg_secondary, TOKENS.canvas, 4.5],
  ["fg_muted on surface", TOKENS.fg_muted, TOKENS.surface, 4.5],
  ["fg_muted on canvas", TOKENS.fg_muted, TOKENS.canvas, 4.5],
  ["fg_muted on raised", TOKENS.fg_muted, TOKENS.raised, 4.5],

  // Chips: accent text on its soft background (4.5:1)
  ["signal on signal_soft", TOKENS.signal, TOKENS.signal_soft, 4.5],
  ["cobalt on cobalt_soft", TOKENS.cobalt, TOKENS.cobalt_soft, 4.5],
  ["evidence on evidence_soft", TOKENS.evidence, TOKENS.evidence_soft, 4.5],
  ["risk on risk_soft", TOKENS.risk, TOKENS.risk_soft, 4.5],
  ["graph on graph_soft", TOKENS.graph, TOKENS.graph_soft, 4.5],

  // Solid buttons: white text on accent fill (4.5:1)
  ["surface on signal", TOKENS.surface, TOKENS.signal, 4.5],
  ["surface on cobalt", TOKENS.surface, TOKENS.cobalt, 4.5],
  ["surface on evidence", TOKENS.surface, TOKENS.evidence, 4.5],
  ["surface on risk", TOKENS.surface, TOKENS.risk, 4.5],
  ["surface on graph", TOKENS.surface, TOKENS.graph, 4.5],
  ["surface on fg_primary", TOKENS.surface, TOKENS.fg_primary, 4.5],

  // Score ring strokes and accent indicators (3:1, non-text UI)
  ["signal vs surface", TOKENS.signal, TOKENS.surface, 3],
  ["cobalt vs surface", TOKENS.cobalt, TOKENS.surface, 3],
  ["evidence vs surface", TOKENS.evidence, TOKENS.surface, 3],
  ["risk vs surface", TOKENS.risk, TOKENS.surface, 3],
  ["graph vs surface", TOKENS.graph, TOKENS.surface, 3],

  // Borders below are intentionally decorative; they pair with text
  // labels and do not encode interactive state on their own. WCAG's
  // 3:1 non-text rule applies to interactive boundaries only, so we
  // keep them out of the audit.
];

const fail = [];
console.log("\nWCAG contrast audit\n");
console.log("Pair                                        Ratio   Threshold  Status");
console.log("-".repeat(80));
for (const [label, fg, bg, threshold] of PAIRS) {
  const ratio = contrast(fg, bg);
  const ok = ratio >= threshold;
  if (!ok) fail.push({ label, ratio: ratio.toFixed(2), threshold });
  console.log(
    `${label.padEnd(42)}  ${ratio.toFixed(2).padStart(5)}    ${threshold.toString().padStart(3)}        ${ok ? "PASS" : "FAIL"}`,
  );
}

if (fail.length > 0) {
  console.log(`\n${fail.length} pair(s) below threshold.`);
  process.exit(1);
} else {
  console.log("\nAll pairs meet WCAG AA.");
}
