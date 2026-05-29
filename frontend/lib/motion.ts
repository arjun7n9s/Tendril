/**
 * Tendril shared motion vocabulary.
 *
 * Premium feel comes from *consistent* motion, not bespoke springs per
 * component. Every animated surface should pull from these named tokens so
 * timing and easing are identical across the app.
 *
 * - EASE_OUT: the house ease-out curve (used for enters, bars, rings).
 * - DUR: a small, named duration scale in seconds.
 * - transition presets: ready-to-spread objects for framer-motion `transition`.
 * - variants: common enter/emphasis variants.
 *
 * Components that must honor `prefers-reduced-motion` should still check
 * `useReducedMotion()` and skip animation; these tokens only standardize the
 * "motion on" path.
 */

import type { Transition, Variants } from "framer-motion";

/** House ease-out cubic. Calm, decisive, never bouncy. */
export const EASE_OUT = [0.22, 1, 0.36, 1] as const;

/** Named duration scale (seconds). */
export const DUR = {
  fast: 0.18,
  base: 0.28,
  slow: 0.5,
  bar: 0.75,
} as const;

/** Standard "enter" tween — fade + small rise. */
export const ENTER: Transition = {
  duration: DUR.base,
  ease: EASE_OUT,
};

/** Snappy spring for panels/banners sliding into place. */
export const SPRING: Transition = {
  type: "spring",
  stiffness: 280,
  damping: 24,
  mass: 0.5,
};

/** One-off emphasis pop (e.g. a value crossing a threshold). */
export const EMPHASIS: Transition = {
  duration: DUR.slow,
  ease: EASE_OUT,
};

export const fadeRise: Variants = {
  hidden: { opacity: 0, y: 6 },
  visible: { opacity: 1, y: 0, transition: ENTER },
};

export const popIn: Variants = {
  hidden: { opacity: 0, scale: 0.97, y: 8 },
  visible: { opacity: 1, scale: 1, y: 0, transition: SPRING },
};

/** A subtle scale pulse [1 → up → 1] for success/emphasis flourishes. */
export const pulseScale = (peak = 1.06) => ({
  scale: [1, peak, 1],
});
