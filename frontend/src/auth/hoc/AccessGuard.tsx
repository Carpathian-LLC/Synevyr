"use client";

import { useAuth } from "@/auth/AuthContext";
import { hasRole, hasAnyRole, hasAnyPermission } from "@/auth/roleUtils";

interface AccessGuardProps {
  role?: string;
  roles?: string[];
  permissions?: string[];
  children: React.ReactNode;
}

export default function AccessGuard({
  role,
  roles = [],
  permissions = [],
  children,
}: AccessGuardProps) {
  const { user } = useAuth();

  if (!user) return null;

  // Consolidate role logic
  const hasRequiredRole = role ? hasRole(user, role) : hasAnyRole(user, roles);
  const hasRequiredPermission = hasAnyPermission(user, permissions);

  // Allow access if user has any matching role OR permission
  if (!hasRequiredRole && !hasRequiredPermission) return null;

  return <>{children}</>;
}
