export function ScanFailedIllustration({ className }: { className?: string }) {
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
      <path d="M70 40l20 20" strokeWidth={2} opacity="0.95" />
      <path d="M90 40l-20 20" strokeWidth={2} opacity="0.95" />
    </svg>
  );
}
