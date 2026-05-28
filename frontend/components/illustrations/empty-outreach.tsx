export function EmptyOutreachIllustration({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 160 96"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={1.4}
      className={className}
      aria-hidden
    >
      <rect x="22" y="22" width="116" height="56" rx="6" opacity="0.4" />
      <path d="M22 30l58 30L138 30" opacity="0.55" />
      <path d="M22 78l34-22" opacity="0.3" />
      <path d="M138 78l-34-22" opacity="0.3" />
      <circle cx="116" cy="22" r="6" fill="currentColor" stroke="none" opacity="0.18" />
    </svg>
  );
}
