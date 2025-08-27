"use client";

import { ComponentType, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../AuthContext";

const LOGIN_PAGE_URL = "/login";
const UNAUTHORIZED_PAGE_URL = "/";

interface RenderWithAuthOptions {
  requiredRoles?: string[];
}

export function renderWithAuth<T extends object>(
  WrappedComponent: ComponentType<T>,
  options?: RenderWithAuthOptions
) {
  return function WithAuthComponent(props: T) {
    const router = useRouter();
    const { user, isAuthenticated, isLoading } = useAuth();

    const [shouldRender, setShouldRender] = useState(false);

    useEffect(() => {
      if (isLoading) return;

      // Not authenticated → redirect to login
      if (!isAuthenticated) {
        router.replace(LOGIN_PAGE_URL);
        return;
      }

      // Missing required roles → redirect to unauthorized
      if (
        options?.requiredRoles &&
        (!user || !options.requiredRoles.some((role) => user.roles.includes(role)))
      ) {
        router.replace(UNAUTHORIZED_PAGE_URL);
        return;
      }

      // All good → allow rendering
      setShouldRender(true);
    }, [isAuthenticated, isLoading, user, router]);

    if (!shouldRender) return null;
    return <WrappedComponent {...props} />;
  };
}
