const LEVEL_LABELS: Record<string, string> = {
  absolute_beginner: "Absolute Beginner",
  beginner: "Beginner",
  elementary: "Elementary",
  intermediate: "Intermediate",
  upper_intermediate: "Upper Intermediate",
  advanced: "Advanced",
  fluent: "Fluent",
};

export function formatLevel(level: string | undefined): string {
  if (!level) return "Absolute Beginner";
  return LEVEL_LABELS[level] ?? level;
}
