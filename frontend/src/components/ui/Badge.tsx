import { ReactNode } from "react";
import clsx from "clsx";

interface BadgeProps {
  children: ReactNode;
  tone?: "indigo" | "gold" | "terracotta" | "palm" | "neutral";
  icon?: ReactNode;
}

const tones = {
  indigo: "bg-indigo/10 text-indigo",
  gold: "bg-gold/15 text-[#8a6a22]",
  terracotta: "bg-terracotta/10 text-terracotta",
  palm: "bg-palm/10 text-palm",
  neutral: "bg-sand text-ink-soft",
};

export function Badge({ children, tone = "neutral", icon }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium",
        tones[tone]
      )}
    >
      {icon}
      {children}
    </span>
  );
}
