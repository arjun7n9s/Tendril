/**
 * Deterministic monogram + color generator for accounts and people.
 *
 * Avoids using third-party brand logos (trademark risk) while still giving
 * each row a recognizable, stable visual identity.
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
  { bg: "bg-[color:color-mix(in_oklab,var(--color-signal)_18%,white)]", fg: "text-[color:var(--color-signal)]" },
  { bg: "bg-[color:color-mix(in_oklab,var(--color-cobalt)_15%,white)]", fg: "text-[color:var(--color-cobalt)]" },
  { bg: "bg-[color:color-mix(in_oklab,var(--color-evidence)_22%,white)]", fg: "text-[color:var(--color-evidence)]" },
  { bg: "bg-[color:color-mix(in_oklab,var(--color-graph)_22%,white)]", fg: "text-[color:var(--color-graph)]" },
  { bg: "bg-[color:color-mix(in_oklab,var(--color-fg-primary)_8%,white)]", fg: "text-[color:var(--color-fg-primary)]" },
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
