"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/auth/AuthContext";

interface AuthButtonsProps {
  isMobile?: boolean;
  onCloseMenu?: () => void;
}

export default function AuthButtons({
  isMobile = false,
  onCloseMenu,
}: AuthButtonsProps) {
  const { isAuthenticated, logout, isLoading } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push("/");
    onCloseMenu?.();
  };

  if (isLoading) return null;

  return (
    <div className="flex items-center space-x-4">
      <span className="hidden lg:inline-block text-gray-500 ml-5">|</span> {/*  <-- DIVIDER BETWEEN PUBLIC NAV AND DASHBOARD/BTNS */}
      {isAuthenticated ? (
        <>
          <Link
            href="/dashboard"
            onClick={() => isMobile && onCloseMenu?.()}
            className="inline-block text-md px-3 py-1 hover:text-blue-200"
          >
            Dashboard
          </Link>
          <button
            onClick={handleLogout}
            className="inline-block text-sm px-3 py-1 bg-red-500 hover:bg-red-600 text-white rounded"
          >
            Logout
          </button>
        </>
      ) : (
        <>
          <Link
            href="/login"
            onClick={() => isMobile && onCloseMenu?.()}
            className="inline-block text-sm px-3 py-1 bg-green-500 hover:bg-green-600 text-white rounded"
          >
            Login
          </Link>
          <Link
            href="/signup"
            onClick={() => isMobile && onCloseMenu?.()}
            className="inline-block text-sm px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded"
          >
            Sign Up
          </Link>
        </>
      )}
    </div>
  );
}
