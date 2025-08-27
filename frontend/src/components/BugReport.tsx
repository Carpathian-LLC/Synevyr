"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { Bug, X } from "lucide-react";
import { fetchWithAuth } from "@/auth/middleware/fetchWithAuth";

export default function BugReport() {
  const [isOpen, setIsOpen] = useState(false);
  const [doing, setDoing] = useState("");
  const [happened, setHappened] = useState("");
  const [sending, setSending] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const open = () => {
    setStatus(null);
    setIsOpen(true);
  };

  const close = () => {
    setIsOpen(false);
    setDoing("");
    setHappened("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    setStatus(null);

    try {
      const res = await fetchWithAuth(`/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        mode: "cors",
        body: JSON.stringify({
          name: "",
          email: "",
          subject: "Bug Report",
          message: `What were you doing?\n${doing}\n\nWhat happened?\n${happened}`,
        }),
      });

      if (res.ok) {
        setStatus("✅ Bug report sent!");
        close();
      } else {
        setStatus("❌ Failed to send. Please try again.");
      }
    } catch (err) {
      console.error("Error sending bug report", err);
      setStatus("❌ Error sending report.");
    } finally {
      setSending(false);
    }
  };

  const modalContent = (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center px-4 bg-black bg-opacity-50 backdrop-blur-sm">
      <div className="relative z-10 w-full max-w-lg bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-300 dark:border-gray-700 p-6">
        <button
          onClick={close}
          aria-label="Close"
          className="absolute top-3 right-4 text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Report a Bug
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="doing"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              What were you doing?
            </label>
            <textarea
              id="doing"
              value={doing}
              onChange={(e) => setDoing(e.target.value)}
              required
              rows={3}
              className="mt-1 w-full px-3 py-2 rounded bg-white bg-opacity-50 dark:bg-gray-700 text-black dark:text-white border border-gray-300 dark:border-gray-600 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          <div>
            <label
              htmlFor="happened"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              What happened?
            </label>
            <textarea
              id="happened"
              value={happened}
              onChange={(e) => setHappened(e.target.value)}
              required
              rows={3}
              className="mt-1 w-full px-3 py-2 rounded bg-white bg-opacity-50 dark:bg-gray-700 text-black dark:text-white border border-gray-300 dark:border-gray-600 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={sending}
              className="inline-flex items-center px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded transition disabled:opacity-50"
            >
              {sending ? (
                "Sending..."
              ) : (
                <>
                  <Bug className="w-4 h-4 mr-2" /> Send Bug Report
                </>
              )}
            </button>
          </div>

          {status && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              {status}
            </p>
          )}
        </form>
      </div>
    </div>
  );

  return (
    <>
      <button
        onClick={open}
        className="inline-flex items-center text-red-500 hover:text-red-600 focus:outline-none"
      >
        <Bug className="w-5 h-5 mr-2" /> Report Bugs
      </button>

      {mounted && isOpen && createPortal(modalContent, document.body)}
    </>
  );
}
