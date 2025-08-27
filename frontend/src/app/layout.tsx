'use client';

import Image from "next/image";
import Link from "next/link";
import NavBar from "@/components/NavBar";
import "@/styles/globals.css";
import ConsentBanner from "@/components/ConsentBanner";
import BugReport from "@/components/BugReport";
import { AuthProvider } from "@/auth/AuthContext";
import ClientRootWrapper from "@/auth/middleware/ClientRootWrapper";
 
export default function RootLayout({ children }: { children: React.ReactNode }) {
  
  return (
    <html lang="en">
      <head />
      <body className="bg-white dark:bg-gray-900 text-white">
        <AuthProvider>
        <ConsentBanner />
        {/* Glassmorphic Header */}
        <header className="fixed top-0 left-0 w-full backdrop-blur-md bg-slate-100/70 border-b border-white/20 shadow-md z-50 dark:bg-slate-900/40">
          <div className="max-w-6xl mx-auto flex justify-between items-center py-4 px-6">
            <Link href="/">
              <Image
                src="/synevyr-crm-light.png"
                alt="Synevyr Logo"
                width={250}
                height={50}
                className="object-contain dark:hidden"
                priority
              />
              <Image
                src="/synevyr-crm-dark.png"
                alt="Synevyr Logo"
                width={250}
                height={50}
                className="object-contain hidden dark:block"
                priority
              />
            </Link>
            <NavBar />
          </div>
        </header>
        
            <ClientRootWrapper>
          <main className="min-h-[100dvh] pt-[75px] flex flex-col">{children}</main>

          <footer className="backdrop-blur-md bg-gray-50 dark:bg-[#121212]/80 border-t border-white/20 shadow-md text-white py-10 px-6 text-sm">
            {/* Divider */}
            <div className="w-full h-px bg-white/20 mb-6"></div>

            {/* Footer Content */}
            <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8 text-center md:text-left">
              <div className="text-black dark:text-white">
                <h4 className="text-base font-semibold">Contact</h4>
                <p className="pt-3">Email us: <a href="mailto:info@carpathian.ai">info@carpathian.ai</a></p>
                <p className="pt-5"><BugReport /></p>
              </div>

              <div className="grid grid-cols-1 gap-2 text-black dark:text-white">
                <h4 className="text-base font-semibold">Quick Links</h4>
                <Link href="/contact"><p>Contact</p></Link>
                <Link href="https://github.com/Carpathian-LLC/Synevyr"><p>Code Repo</p></Link>
                <Link href="https://synevyr.org/public-data"><p>Public Data</p></Link>
                <Link href="/documentation/synevyr-public-data"><p>Public Data Documentation</p></Link>
              </div>
              <div className="text-black dark:text-white">
                <p className="pt-3 text-sm text-gray-400 dark:text-gray-300">
                  Synevyr is an open-source platform developed and maintained by <Link href="https://carpathian.ai"><span className="underline">Carpathian, LLC</span></Link>. 
                  The name reflects its inspiration: Lake Synevyr, situated within the Carpathian Mountains symbolizing a “data lake” within the broader Carpathian ecosystem. 
                  The platform&apos;s source code is freely available for use.
                </p>
                <p className="pt-5">
                  © 2025 <Link href="https://carpathian.ai"><span>Carpathian</span></Link>, LLC. All rights reserved.
                </p>
              </div>
            </div>
          </footer>
          
          </ClientRootWrapper>
      </AuthProvider>
      </body>
    </html>
  );
}
