import { ReactNode } from "react";

export function SectionHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 mb-7">
      <div>
        {eyebrow && <p className="text-sm text-terracotta font-medium mb-1">{eyebrow}</p>}
        <h1 className="font-display text-3xl text-ink">{title}</h1>
        {description && <p className="mt-1.5 text-ink-soft max-w-lg">{description}</p>}
      </div>
      {action}
    </div>
  );
}
