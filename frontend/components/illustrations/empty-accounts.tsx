/**
 * Empty state illustration for /accounts.
 *
 * All seven illustrations follow the same constraints from
 * kiro/kiro-frontend-assets-plan.md §5: flat, abstract, single-stroke, no
 * literal devices or human figures. Each picks up the active accent
 * via currentColor so it shifts with our token palette.
 */
export function EmptyAccountsIllustration({ className }: { className?: string }) {
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
      <rect x="14" y="20" width="132" height="60" rx="6" opacity="0.35" />
      <path d="M30 38h60" opacity="0.55" />
      <path d="M30 50h44" opacity="0.4" />
      <path d="M30 62h32" opacity="0.3" />
      <circle cx="118" cy="50" r="10" opacity="0.55" />
      <path d="M125 57l8 8" opacity="0.55" />
    </svg>
  );
}
