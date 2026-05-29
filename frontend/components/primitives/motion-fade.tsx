"use client";

import { motion, useReducedMotion } from "framer-motion";
import * as React from "react";

import { DUR, EASE_OUT } from "@/lib/motion";

type MotionFadeProps = {
  delay?: number;
  duration?: number;
  className?: string;
  children: React.ReactNode;
  as?: keyof typeof motion;
};

/**
 * Subtle fade-and-rise used when content settles into place: signal
 * cards on a scan completion, KPI strips on first paint, etc.
 *
 * Honors `prefers-reduced-motion`: when set, the component renders
 * its children with no animation rather than reducing duration. This
 * matches the architecture's accessibility rule that motion respects
 * the user's preference, plus the already-disabled global transitions
 * in app/globals.css.
 */
export function MotionFade({
  delay = 0,
  duration = DUR.base,
  className,
  children,
  as = "div",
}: MotionFadeProps) {
  const reduce = useReducedMotion();
  const Tag = motion[as] as typeof motion.div;

  if (reduce) {
    return <div className={className}>{children}</div>;
  }

  return (
    <Tag
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration, ease: EASE_OUT }}
      className={className}
    >
      {children}
    </Tag>
  );
}
