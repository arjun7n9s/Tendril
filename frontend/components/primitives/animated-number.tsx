"use client";

import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "framer-motion";

type AnimatedNumberProps = {
  value: number;
  durationMs?: number;
  className?: string;
};

/**
 * Counts up/down to `value` with an ease-out curve. Honors reduced-motion by
 * snapping straight to the target. Used for the headline account score so a
 * scan visibly "moves the number."
 */
export function AnimatedNumber({ value, durationMs = 700, className }: AnimatedNumberProps) {
  const reduce = useReducedMotion();
  const [display, setDisplay] = useState(value);
  const fromRef = useRef(value);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (reduce) {
      // Snap on the next frame (not synchronously) so we don't trigger a
      // cascading render from within the effect body.
      fromRef.current = value;
      rafRef.current = requestAnimationFrame(() => setDisplay(value));
      return () => {
        if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      };
    }
    const from = fromRef.current;
    const to = value;
    if (from === to) return;
    const start = performance.now();

    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - t, 3); // ease-out cubic
      setDisplay(Math.round(from + (to - from) * eased));
      if (t < 1) {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        fromRef.current = to;
      }
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [value, durationMs, reduce]);

  return (
    <span className={className} aria-label={String(value)}>
      {display}
    </span>
  );
}
