"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { name: "Account", href: "/dashboard/settings/account" },
  { name: "Support", href: "/dashboard/settings/support" },
] as const;

export const TabNav: React.FC = () => {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-30 mb-6 w-full bg-white/70 dark:bg-gray-900/30 backdrop-blur-md border-b border-gray-300 dark:border-gray-800 px-4 py-2">
      {/* Mobile: dropdown */}
      <div className="sm:hidden">
        <select
          className="w-full px-3 py-2 rounded-md bg-gray-100 dark:bg-gray-800 text-sm dark:text-white"
          value={pathname}
          onChange={(e) => {
            window.location.href = e.target.value;
          }}
        >
          {tabs.map((tab) => (
            <option key={tab.name} value={tab.href}>
              {tab.name}
            </option>
          ))}
        </select>
      </div>

      {/* Desktop: horizontal tabs */}
      <ul className="hidden sm:flex w-full divide-x divide-gray-300 dark:divide-gray-700 rounded-lg overflow-hidden text-sm">
        {tabs.map((tab) => {
          const isActive = pathname === tab.href;
          return (
            <li key={tab.name} className="flex-1">
              <Link
                href={tab.href}
                shallow
                className={`block w-full text-center px-2 py-2 transition-all duration-150
                  ${
                    isActive
                      ? "bg-gray-600 text-white shadow-inner"
                      : "bg-gray-100 dark:bg-gray-800/60 text-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700"
                  }`}
              >
                {tab.name}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
};
