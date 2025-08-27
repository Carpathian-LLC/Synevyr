"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import AuthButtons from "@/components/LoginLogoutButtons";

const navLinkColors: { [key: string]: string } = {
  "/company":    "text-pink-600",
  "/documentation": "text-yellow-500",
  "/dashboard":    "text-blue-500",
};

export default function NavBar() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  const baseLinks = [
    { href: "/company",      label: "Company" },
    { href: "/documentation", label: "Documentation" },
  ];

  const renderBaseLinks = (isMobile = false) =>
    baseLinks.map(({ href, label }) => {
      const isActive = pathname.startsWith(href);
      const activeClass = isActive ? navLinkColors[href] : "";
      const extraClass = isMobile ? "py-2" : "hover:text-blue-500";
      return (
        <Link
          key={href}
          href={href}
          onClick={() => isMobile && setMenuOpen(false)}
          className={`transition block ${activeClass} ${extraClass}`}
        >
          {label}
        </Link>
      );
    });

  const closeMenu = () => setMenuOpen(false);

  return (
    <div className="relative">
      {/* Desktop Navigation */}
      <nav className="hidden lg:flex items-center text-gray-700 dark:text-gray-200">
        {/* Centered nav items */}
        <div className="flex-1 flex justify-center space-x-6">
          {renderBaseLinks()}
        </div>

        {/* Divider + Dashboard + Sign Up + AuthButtons */}
        <div className="flex items-center space-x-4 pr-4">
          <AuthButtons />
        </div>
      </nav>

      {/* Mobile Hamburger and Menu */}
      <div className="lg:hidden relative z-50">
        {/* Hamburger Toggle */}
        <div className="flex items-center justify-between px-4 py-2">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="text-gray-700 dark:text-gray-200 focus:outline-none"
            aria-label="Toggle navigation menu"
          >
            {menuOpen ? (
              /* Close icon */
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none"
                   viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              /* Hamburger icon */
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none"
                   viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>

        {menuOpen && (
          <div className="fixed inset-0 z-40">
            {/* Backdrop */}
            <div
              className="absolute inset-0 bg-black bg-opacity-50 backdrop-blur-sm"
              onClick={closeMenu}
            />

            {/* Drawer */}
            <div className="absolute top-0 left-0 w-full bg-white dark:bg-gray-900 p-6
                            rounded-b-2xl shadow-xl animate-slide-down z-50">
              {/* Close Button */}
              <div className="flex justify-end mb-4">
                <button
                  onClick={closeMenu}
                  className="text-gray-700 dark:text-gray-300 focus:outline-none"
                  aria-label="Close menu"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none"
                       viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="flex items-center flex-col space-y-4 text-lg text-gray-800 dark:text-gray-100">
                {renderBaseLinks(true)}

                {/* Divider */}
                <div className="w-full border-t border-gray-300 dark:border-gray-700 my-2" />

                <AuthButtons isMobile onCloseMenu={closeMenu} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
