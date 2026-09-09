import clsx from "clsx";

interface ProgressBarProps {
  value: number; // 0-100
  tone?: "indigo" | "gold" | "palm";
  className?: string;
}

const tones = {
  indigo: "bg-indigo",
  gold: "bg-gold",
  palm: "bg-palm",
};

export function ProgressBar({ value, tone = "indigo", className }: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, value));
  return (
    <div
      className={clsx("h-2 w-full rounded-full bg-sand", className)}
      role="progressbar"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className={clsx("h-full rounded-full transition-[width] duration-500", tones[tone])}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
