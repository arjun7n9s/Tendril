export function EmptySignalsIllustration({ className }: { className?: string }) {
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
      <circle cx="80" cy="50" r="6" opacity="0.7" />
      <circle cx="80" cy="50" r="18" opacity="0.45" />
      <circle cx="80" cy="50" r="30" opacity="0.25" />
      <circle cx="80" cy="50" r="44" opacity="0.12" />
      <path d="M80 6v6" opacity="0.4" />
      <path d="M80 88v6" opacity="0.4" />
      <path d="M28 50h6" opacity="0.4" />
      <path d="M126 50h6" opacity="0.4" />
    </svg>
  );
}
