import { ReactNode } from "react";
import { NavRail } from "./NavRail";
import { MobileTabBar } from "./MobileTabBar";
import { MobileTopBar } from "./MobileTopBar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen bg-paper">
      <NavRail />
      <div className="flex-1 min-w-0">
        <MobileTopBar />
        <main className="px-4 py-6 pb-24 lg:px-10 lg:py-10 lg:pb-10 max-w-5xl mx-auto">
          {children}
        </main>
        <MobileTabBar />
      </div>
    </div>
  );
}
