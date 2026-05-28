/**
 * Deterministic monogram + color generator for accounts and people.
 *
 * Avoids using third-party brand logos (trademark risk) while still giving
 * each row a recognizable, stable visual identity.
 *
 * The palette uses the brand neutral surface as the background and only
 * varies the foreground accent, so every combination clears WCAG AA on
 * white-ish surfaces (each accent was tuned to >=4.5:1 in
 * scripts/contrast-audit.mjs). A subtle hairline ring keeps the tile
 * legible against canvas/raised parents.
 */

export function initialsFor(name: string, max = 2): string {
  const words = name
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .split(/\s+/)
    .filter(Boolean);
  if (words.length === 0) return "?";
  if (words.length === 1) return words[0]!.slice(0, max).toUpperCase();
  return words
    .slice(0, max)
    .map((word) => word[0]!.toUpperCase())
    .join("");
}

const MONOGRAM_PALETTE: Array<{ bg: string; fg: string }> = [
  { bg: "bg-[color:var(--color-raised)]", fg: "text-[color:var(--color-signal)]" },
  { bg: "bg-[color:var(--color-raised)]", fg: "text-[color:var(--color-cobalt)]" },
  { bg: "bg-[color:var(--color-raised)]", fg: "text-[color:var(--color-evidence)]" },
  { bg: "bg-[color:var(--color-raised)]", fg: "text-[color:var(--color-graph)]" },
  { bg: "bg-[color:var(--color-raised)]", fg: "text-[color:var(--color-fg-primary)]" },
];

function hashString(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 31 + value.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

export function paletteFor(seed: string): { bg: string; fg: string } {
  const idx = hashString(seed) % MONOGRAM_PALETTE.length;
  return MONOGRAM_PALETTE[idx]!;
}
