// src/auth/middleware/fetchWithAuth.tsx

// Handles/wraps ALL API calls and checks the session to ensure the cookie is valid. 
import { triggerUnauthorizedModal } from "./unauthorizedModalTrigger";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export async function fetchWithAuth(path: string, options: RequestInit = {}) {
  const fullUrl = `${API_BASE_URL}${path}`;
  const isFormData = options.body instanceof FormData;

  const res = await fetch(fullUrl, {
    ...options,
    credentials: "include",
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });

  if (res.status === 401 || res.status === 403) {
    if (typeof window !== "undefined") {
      setTimeout(() => {
        triggerUnauthorizedModal(path, res.status);
      }, 0);
    }
    throw new Error("Unauthorized");
  }

  return res;
}
