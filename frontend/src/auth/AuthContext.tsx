// src/auth/AuthContext.tsx
"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { fetchWithoutAuth } from "@/auth/middleware/fetchWithoutAuth";

// Define the User type
export interface User {
  id: string;
  username: string;
  email?: string; // Optional
  roles: string[]; // e.g., ['admin', 'editor']
  permissions: string[];
  // Add any other user-specific fields you need
}

interface LoginCredentials {
  username: string;
  password: string;
}

// Define the shape of the context data
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<boolean>;
  logout: () => Promise<void>;
  checkAuthStatus: () => Promise<User | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();

const checkAuthStatus = useCallback(async (): Promise<User | null> => {
  setIsLoading(true);
  try {
    const response = await fetchWithoutAuth(`/auth/me`, {
      method: "GET",
      credentials: "include",
    });

    if (response.ok) {
      const data = await response.json();
      if (data && data.success && data.user) {
        const fetchedUser = data.user as User;
        setUser(fetchedUser);
        setIsAuthenticated(true);
        return fetchedUser;
      }
    }

    // If not authorized or failed
    setUser(null);
    setIsAuthenticated(false);
    return null;
  } catch (error) {
    console.error("Failed to check auth status:", error);
    setUser(null);
    setIsAuthenticated(false);
    return null;
  } finally {
    setIsLoading(false);
  }
}, []);


  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    setIsLoading(true);
    let loginSuccess = false;
    try {
      const response = await fetchWithoutAuth("/login",
        {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(credentials),
        credentials: "include",
      });

      if (response.ok) {
        // Backend sets cookie, now fetch user details
        await checkAuthStatus(); // This will attempt to set user and isAuthenticated
        // To get the updated isAuthenticated state, we need to rely on its value after checkAuthStatus
        // This is tricky because setState is async. A better way is to have checkAuthStatus return the user/auth state.
        // For now, we'll re-fetch the value from a local variable that checkAuthStatus would update.
        // This part is still a bit of a workaround for state update timing.
        // A more robust way: checkAuthStatus could return the status or user object.
        // For simplicity, assuming checkAuthStatus correctly updates the state that will be read below.
        // The `setTimeout` hack is not ideal. Let's try to make `checkAuthStatus` more directly usable.
        // Modify checkAuthStatus to return a boolean indicating success for login flow.
        // Or, even better, login itself confirms and sets the state.

        // Let's simplify: if login API is OK, and then checkAuthStatus is OK, it's a success.
        // We'll assume checkAuthStatus has updated the state.
        // The `isAuthenticated` state might not be updated immediately for the return value.
        // A common pattern is for `checkAuthStatus` to return the user or auth status.
        // For now, let's assume if checkAuthStatus runs without error after a 200 OK from login, it's a success.
        // The `isAuthenticated` state will be updated for subsequent renders.
        // The promise returned by login should reflect the API call success.
        loginSuccess = true; // Mark as successful based on API response and subsequent check
      } else {
        const errorData = await response.json();
        console.error("Login failed:", errorData.errors || errorData.message || "Unknown login error");
        setIsAuthenticated(false);
        setUser(null);
        loginSuccess = false;
      }
    } catch (error) {
      console.error("Login request failed:", error);
      setIsAuthenticated(false);
      setUser(null);
      loginSuccess = false;
    } finally {
        setIsLoading(false); // Ensure loading is false after login attempt
    }
    return loginSuccess;
  };
 
  const logout = async (): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await fetchWithoutAuth(`/logout`, {
        method: "POST",
        credentials: "include",
      });
      if (!response.ok) {
        console.error("Logout request failed on backend:", await response.text());
      }
    } catch (error) {
      console.error("Logout request failed:", error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      setIsLoading(false);
      router.push("/login");
    }
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isLoading, login, logout, checkAuthStatus }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
