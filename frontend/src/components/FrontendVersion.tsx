"use client";

import React, { useEffect, useState } from "react";
import { fetchWithoutAuth } from "@/auth/middleware/fetchWithoutAuth";

const FrontendVersion: React.FC = () => {
  const [version, setVersion] = useState<string | null>(null);

  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const res = await fetchWithoutAuth("/meta/version?type=frontend");
        if (res.ok) {
          const data = await res.json();
          setVersion(data.frontend_version);
        }
      } catch (err) {
        console.error("Failed to fetch frontend version:", err);
      }
    };

    fetchVersion();
  }, []);

  if (!version) return null;

  return (
    <span className="text-xs text-gray-500 dark:text-gray-400 mt-12">
      Frontend version: {version}
    </span>
  );
};

export default FrontendVersion;
