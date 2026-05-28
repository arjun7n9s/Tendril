import { cn } from "@/lib/utils/cn";

type SectionHeadingProps = {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
};

export function SectionHeading({ title, description, action, className }: SectionHeadingProps) {
  return (
    <div
      className={cn(
        "flex items-end justify-between gap-3 border-b border-[color:var(--color-border-default)] pb-2",
        className,
      )}
    >
      <div className="flex flex-col gap-0.5">
        <h2 className="text-[13px] font-semibold tracking-[0.04em] uppercase text-[color:var(--color-fg-secondary)]">
          {title}
        </h2>
        {description ? (
          <p className="text-[13px] text-[color:var(--color-fg-muted)]">{description}</p>
        ) : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}
