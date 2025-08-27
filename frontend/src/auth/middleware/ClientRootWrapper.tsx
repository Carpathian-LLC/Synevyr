"use client";

import UnauthorizedModalProvider from "@/auth/middleware/UnauthorizedModalProvider";

export default function ClientRootWrapper({ children }: { children: React.ReactNode }) {
  return <UnauthorizedModalProvider>{children}</UnauthorizedModalProvider>;
}
