import { ButtonHTMLAttributes, ReactNode } from "react";
import clsx from "clsx";

type Variant = "primary" | "secondary" | "ghost";
type Size = "md" | "sm";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  icon?: ReactNode;
}

const variants: Record<Variant, string> = {
  primary:
    "bg-indigo text-paper hover:bg-indigo-deep active:scale-[0.98]",
  secondary:
    "bg-transparent text-indigo border border-indigo/30 hover:border-indigo hover:bg-indigo/5",
  ghost: "bg-transparent text-ink-soft hover:text-ink hover:bg-sand/60",
};

const sizes: Record<Size, string> = {
  md: "px-5 py-2.5 text-[15px]",
  sm: "px-3.5 py-1.5 text-sm",
};

export function Button({
  variant = "primary",
  size = "md",
  icon,
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-full font-semibold transition-all duration-150 disabled:opacity-40 disabled:pointer-events-none",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {icon}
      {children}
    </button>
  );
}
