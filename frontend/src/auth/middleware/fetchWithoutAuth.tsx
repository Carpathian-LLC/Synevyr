
// Default for any NON authenticated API calls. This just makes the fetch call easier. 

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export async function fetchWithoutAuth(path: string, options: RequestInit = {}) {
  const fullUrl = `${API_BASE_URL}${path}`;
  
  const res = await fetch(fullUrl, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  return res;
}
