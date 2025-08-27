"use client";

import React, { useState, useEffect } from "react";
import { fetchWithAuth } from "@/auth/middleware/fetchWithAuth";
import BugReport from "@/components/BugReport";

type Item = { id: string; title: string; description: string };

interface VersionResponse {
  backend_version: string;
  frontend_version: string;
  changelog: Item[];
  known_issues: Item[];
}

const SupportPage: React.FC = () => {
  const [versions, setVersions] = useState({ frontend: "", backend: "" });
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    const fetchData = async () => {
      try {
        const res = await fetchWithAuth("/meta/version");

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: VersionResponse = await res.json();

        if (!active) return;

        setVersions({
          frontend: data.frontend_version,
          backend: data.backend_version,
        });
      } catch (e) {
        console.error(e);
        if (active) setError("Failed to load support data.");
      }
    };

    fetchData();
    return () => {
      active = false;
    };
  }, []);


  if (error) {
    return (
      <div className="p-8">
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  return (
<div className="p-6 space-y-10">
  {/* Header */}
    <h2 className="text-xl font-semibold text-black dark:text-white">
      Support Center
    </h2>
    <p className="text-sm text-gray-600 dark:text-gray-400">
      Get the latest updates, known issues, and support resources.
    </p>

  {/* Version Info Card */}
  {/* <section className="mb-10">
    <div className="bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-300 dark:border-gray-700 rounded-2xl shadow-xl p-6">
      <h2 className="text-xl font-semibold text-black dark:text-white mb-2">Other Card Here</h2>
      <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-1">
        <li>Item 1</li>
        <li>Item 2</li>
      </ul>
    </div>
  </section> */}

  {/* Contact Info Card */}
  <section className="mb-10">
    <div className="bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-300 dark:border-gray-700 rounded-2xl shadow-md p-6">
      <h2 className="text-md font-semibold text-black dark:text-white mb-2">Contact Support</h2>
      <p className="text-gray-600 dark:text-gray-300 mb-1 text-sm">Phone: (515) 344-3081</p>
      <p className="text-gray-600 dark:text-gray-300 mb-1 text-sm">
        Email: <a href="mailto:info@carpathian.ai" className="text-blue-500 hover:underline">info@carpathian.ai</a>
      </p>
      <div className="mt-4 text-sm"><BugReport /></div>
    </div>
  </section>

        {/* Version Info Card */}
  <section className="mb-10">
    <div className="bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-300 dark:border-gray-700 rounded-2xl shadow-md p-6">
      <h2 className="text-xl font-semibold text-black dark:text-white mb-2">System Version Info</h2>
      <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-1">
        <li>Frontend Version: <strong>{versions.frontend}</strong></li>
        <li>Backend Version: <strong>{versions.backend}</strong></li>
      </ul>
    </div>
  </section>
    </div>
  );
};

export default SupportPage;
