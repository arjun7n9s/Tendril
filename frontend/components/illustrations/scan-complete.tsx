export function ScanCompleteIllustration({ className }: { className?: string }) {
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
      <circle cx="80" cy="50" r="34" opacity="0.4" />
      <circle cx="80" cy="50" r="22" opacity="0.55" />
      <path d="M68 50l9 10 17-20" opacity="0.95" strokeWidth={2} />
    </svg>
  );
}
