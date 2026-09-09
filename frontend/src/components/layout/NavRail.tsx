"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import clsx from "clsx";
import { navItems } from "@/lib/nav-items";
import { Flame, LogOut } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export function NavRail() {
  const pathname = usePathname();
  const router = useRouter();
  const { profile, logout } = useAuth();

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:shrink-0 border-r border-line bg-indigo-deep text-paper/90 min-h-screen sticky top-0">
      <div className="px-6 pt-8 pb-6">
        <Link href="/dashboard" className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-gold text-indigo-deep font-display text-lg font-bold">
            I
          </span>
          <span className="font-display text-xl text-paper">Igbo AI</span>
        </Link>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {navItems.map((item) => {
          const active = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-[15px] font-medium transition-colors",
                active
                  ? "bg-paper/10 text-paper"
                  : "text-paper/60 hover:text-paper hover:bg-paper/5"
              )}
            >
              <Icon size={19} strokeWidth={2} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mx-4 mb-3 rounded-xl bg-paper/5 px-4 py-3.5 flex items-center gap-2.5">
        <Flame size={18} className="text-gold" />
        <div className="text-sm">
          <p className="font-semibold text-paper">{profile?.current_streak ?? 0}-day streak</p>
          <p className="text-paper/50 text-xs">Learn today to keep it going</p>
        </div>
      </div>
      <button
        onClick={handleLogout}
        className="mx-4 mb-6 flex items-center gap-2 px-3.5 py-2 text-sm text-paper/50 hover:text-paper transition-colors"
      >
        <LogOut size={16} />
        Log out
      </button>
    </aside>
  );
}
