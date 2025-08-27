// src/app/public-data/page.tsx
"use client";

import { useState } from "react";
import Link from "next/link";
import { Clipboard, Check } from "lucide-react";

export default function PublicDataPage() {
  const [copiedLink, setCopiedLink] = useState<string | null>(null);

  const handleCopy = async (url: string) => {
    try {
      await navigator.clipboard.writeText(url);
      setCopiedLink(url);
      setTimeout(() => setCopiedLink(null), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  const endpoints = [
    {
      url: "https://api.synevyr.org/public/user_customers",
      description: "Customer records for demo analytics.",
    },
    {
      url: "https://api.synevyr.org/public/meta_leads",
      description: "Marketing lead data for testing.",
    },
    {
      url: "https://api.synevyr.org/public/wc_orders",
      description: "E-commerce order data.",
    },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white px-6 py-16">
      <div className="max-w-5xl mx-auto">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-blue-500 mb-4">
            Synevyr Public Data
          </h1>
          <p className="text-lg text-gray-300">
            Open-source synthetic datasets for research, analytics, and demos —
            no authentication required.
          </p>
        </div>

        {/* Glassmorphism Content Card */}
        <div className="bg-white bg-opacity-10 dark:bg-gray-800 dark:bg-opacity-40 backdrop-blur-md border border-gray-700 rounded-2xl shadow-xl p-8">
          <h2 className="text-2xl font-semibold text-blue-400 mb-4">
            Open Access API
          </h2>
          <p className="text-gray-300 mb-6">
            The Synevyr Public Data API gives you instant access to sample
            datasets without needing API keys or authentication. Perfect for
            testing integrations, learning analytics, and exploring data
            pipelines.
          </p>

          <div className="mb-8">
            <h3 className="text-xl font-semibold text-pink-400 mb-2">
              Example Query
            </h3>
            <pre className="bg-black bg-opacity-40 p-4 rounded-lg text-sm overflow-x-auto">
              {`curl "https://api.synevyr.org/public/user_customers?page=1&page_size=50"`}
            </pre>
          </div>

          {/* Endpoints Section */}
          <div>
            <h3 className="text-xl font-semibold text-blue-400 mb-4">
              Available Endpoints
            </h3>
            <ul className="space-y-3 text-gray-300">
              {endpoints.map((endpoint) => (
                <li key={endpoint.url} className="flex items-center gap-3">
                  <code className="bg-black text-blue-400 px-2 py-1 rounded font-mono">
                    {endpoint.url}
                  </code>
                  <button
                    onClick={() => handleCopy(endpoint.url)}
                    className="p-1 rounded-md bg-gray-800 hover:bg-gray-700 transition"
                    aria-label="Copy to clipboard"
                  >
                    {copiedLink === endpoint.url ? (
                      <Check className="w-4 h-4 text-green-400" />
                    ) : (
                      <Clipboard className="w-4 h-4 text-gray-400" />
                    )}
                  </button>
                  <span className="text-gray-400">{endpoint.description}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Docs Link */}
          <div className="mt-10">
            <Link
              href="/documentation/synevyr-public-data"
              className="inline-block px-6 py-3 rounded-xl bg-blue-500 hover:bg-blue-600 text-white font-semibold transition shadow-lg hover:shadow-[0_0_20px_rgba(59,130,246,0.6)]"
            >
              Read Full Documentation
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
