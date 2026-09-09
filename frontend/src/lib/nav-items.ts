import {
  LayoutDashboard,
  BookOpen,
  Dumbbell,
  MessageCircle,
  Layers,
  RotateCcw,
  TrendingUp,
  User,
  LucideIcon,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

// Ordered to mirror the learner's journey: Dashboard -> Learn -> Practice ->
// Conversation, with Vocabulary/Review/Progress/Profile as supporting sections.
export const navItems: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/learn", label: "Learn", icon: BookOpen },
  { href: "/practice", label: "Practice", icon: Dumbbell },
  { href: "/conversation", label: "Conversation", icon: MessageCircle },
  { href: "/vocabulary", label: "Vocabulary", icon: Layers },
  { href: "/review", label: "Review", icon: RotateCcw },
  { href: "/progress", label: "Progress", icon: TrendingUp },
  { href: "/profile", label: "Profile", icon: User },
];

// Primary journey shown as the mobile tab bar (subset — full set lives in the rail).
export const primaryNavItems: NavItem[] = [
  navItems[0],
  navItems[1],
  navItems[2],
  navItems[3],
  navItems[6],
];
