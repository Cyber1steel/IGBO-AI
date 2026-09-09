import Link from "next/link";
import { Flame } from "lucide-react";

export function MobileTopBar() {
  return (
    <header className="lg:hidden sticky top-0 z-30 flex items-center justify-between border-b border-line bg-paper/95 backdrop-blur px-4 py-3">
      <Link href="/dashboard" className="flex items-center gap-2">
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo text-paper font-display text-sm font-bold">
          I
        </span>
        <span className="font-display text-lg">Igbo AI</span>
      </Link>
      <div className="flex items-center gap-1 text-sm font-semibold text-terracotta">
        <Flame size={16} />
        6
      </div>
    </header>
  );
}
