"use client";
import React from "react";
import { TabNav } from "@/components/TabNav";

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen dark:bg-gray-900 p-4 sm:p-8">
      {/* Responsive Tab Nav Container */}
      <div className="overflow-x-auto -mx-4 sm:mx-0">
        <div className="px-4 sm:px-0 min-w-max">
          <TabNav />
        </div>
      </div>

      {/* Sub-page content */}
      <main className="mt-8">{children}</main>
    </div>
  );
}
