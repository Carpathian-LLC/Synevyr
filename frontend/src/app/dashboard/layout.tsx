"use client";

import DashboardSidebar from "@/components/dashboard/DashboardSidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex flex-1">
        <DashboardSidebar />
          <main className="flex-1 p-6 bg-white dark:bg-gray-900">
            <div className="max-w-screen-xl mx-auto min-h-full">
              {children}
            </div>
          </main>
      </div>
    </div>
  );
}
