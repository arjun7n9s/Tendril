export function ErrorStateIllustration({ className }: { className?: string }) {
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
      <path d="M80 16l60 64H20z" opacity="0.4" />
      <path d="M80 38v18" opacity="0.7" />
      <circle cx="80" cy="68" r="2" fill="currentColor" stroke="none" opacity="0.7" />
    </svg>
  );
}
