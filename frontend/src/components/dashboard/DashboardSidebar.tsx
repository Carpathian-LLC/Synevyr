"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/auth/AuthContext";
import AccessGuard from "@/auth/hoc/AccessGuard";

interface NavItem {
  name: string;
  base: string;
  href: string;
  role?: string;
  permission?: string;
  newTab?: boolean;
}

const mainNav: NavItem[] = [
  { name: "Home", base: "home", href: "/dashboard" },
];

const supportNav: NavItem[] = [
  { name: "Connect Data", base: "data", href: "/dashboard/connect-data" },
  { name: "Settings", base: "settings", href: "/dashboard/settings" },
];

const DashboardSidebar: React.FC = () => {
  const { user } = useAuth();
  const pathname = usePathname();

  const activeHref =
    [...mainNav, ...supportNav]
      .filter((item) => pathname.startsWith(item.href))
      .sort((a, b) => b.href.length - a.href.length)[0]?.href;

  const renderNavGroup = (items: NavItem[]) =>
    items.map((item) => {
      const isActive = item.href === activeHref;
      const link = item.newTab ? (
        <a
          key={item.name}
          href={item.href}
          target="_blank"
          rel="noopener noreferrer"
          className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
            isActive
              ? "bg-gray-300 dark:bg-gray-700 text-black dark:text-white"
              : "hover:bg-gray-200 dark:hover:bg-gray-700"
          }`}
        >
          <Image
            src={`/nav-icons/${item.base}-dark.png`}
            alt={item.name}
            width={40}
            height={40}
            className={`h-10 w-10 transition-transform transform group-hover:scale-110 mr-3 dark:hidden ${
              isActive ? "scale-110" : ""
            }`}
          />
          <Image
            src={`/nav-icons/${item.base}-light.png`}
            alt={item.name}
            width={40}
            height={40}
            className={`h-10 w-10 transition-transform transform group-hover:scale-110 mr-3 hidden dark:block ${
              isActive ? "scale-110" : ""
            }`}
          />
          <span className="hidden md:block text-black dark:text-white">{item.name}</span>
        </a>
      ) : (
        <Link
          key={item.name}
          href={item.href}
          className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
            isActive
              ? "bg-gray-300 dark:bg-gray-700 text-black dark:text-white"
              : "hover:bg-gray-200 dark:hover:bg-gray-700"
          }`}
        >
          <Image
            src={`/nav-icons/${item.base}-dark.png`}
            alt={item.name}
            width={40}
            height={40}
            className={`h-10 w-10 transition-transform transform group-hover:scale-110 mr-3 dark:hidden ${
              isActive ? "scale-110" : ""
            }`}
          />
          <Image
            src={`/nav-icons/${item.base}-light.png`}
            alt={item.name}
            width={40}
            height={40}
            className={`h-10 w-10 transition-transform transform group-hover:scale-110 mr-3 hidden dark:block ${
              isActive ? "scale-110" : ""
            }`}
          />
          <span className="hidden md:block text-black dark:text-white">{item.name}</span>
        </Link>
      );

      if (item.role || item.permission) {
        return (
          <AccessGuard
            key={item.name}
            role={item.role}
            permissions={item.permission ? [item.permission] : []}
          >
            {link}
          </AccessGuard>
        );
      }
      return link;
    });

  return (
    <aside className="min-h-screen w-20 md:w-64 bg-gray-100 dark:bg-gray-800 flex flex-col">
      <h1 className="flex-shrink-0 flex items-center justify-center text-black dark:text-white h-16 border-b border-gray-300 dark:border-gray-700">
        {user?.username || "[Loading user]"}
      </h1>
      <nav className="flex-1 px-2 py-4 space-y-4">

        {/* Main Section */}
        <div className="space-y-1">{renderNavGroup(mainNav)}</div>

        <hr className="border-t border-gray-300 dark:border-gray-700" />

        {/* Settings Section */}
        <div className="pt-2 space-y-1">{renderNavGroup(supportNav)}</div>
      </nav>
    </aside>
  );
};

export default DashboardSidebar;
