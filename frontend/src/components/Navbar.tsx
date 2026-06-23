"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Crosshair, TrendingUp, List, Shield } from "lucide-react";

const links = [
  { href: "/", label: "Dashboard", icon: Crosshair },
  { href: "/players", label: "Jogadores", icon: List },
  { href: "/value-bets", label: "Value Bets", icon: TrendingUp },
  { href: "/admin", label: "Admin", icon: Shield },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="border-b border-surface-700 bg-surface-800/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2 group">
            <Crosshair className="w-6 h-6 text-accent-400" />
            <span className="text-xl font-bold text-white group-hover:text-accent-400 transition-colors">
              ShotSaaS
            </span>
          </Link>

          <div className="flex items-center gap-1">
            {links.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-primary-600/20 text-primary-300"
                      : "text-gray-400 hover:text-gray-200 hover:bg-surface-700"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{link.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
