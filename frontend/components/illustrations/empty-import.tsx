export function EmptyImportIllustration({ className }: { className?: string }) {
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
      <rect x="40" y="20" width="80" height="60" rx="6" opacity="0.35" />
      <path d="M58 36h44" opacity="0.55" />
      <path d="M58 48h36" opacity="0.45" />
      <path d="M58 60h28" opacity="0.35" />
      <path d="M80 6v22" opacity="0.55" />
      <path d="M72 22l8 8 8-8" opacity="0.55" />
    </svg>
  );
}
