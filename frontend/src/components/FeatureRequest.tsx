"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { Lightbulb, X } from "lucide-react";
import { fetchWithoutAuth} from "@/auth/middleware/fetchWithoutAuth"

export default function FeatureRequest() {
  const [isOpen, setIsOpen] = useState(false);
  const [feature, setFeature] = useState("");
  const [reason, setReason] = useState("");
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
    setFeature("");
    setReason("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    setStatus(null);

    try {
      const res = await fetchWithoutAuth(
        `/contact`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          mode: "cors",
          body: JSON.stringify({
            name: "",
            email: "",
            subject: "Feature Request",
            message: `Feature Idea:\n${feature}\n\nWhy it's useful:\n${reason}`,
          }),
        }
      );

      if (res.ok) {
        setStatus("✅ Feature request sent. Thank you!");
        close();
      } else {
        setStatus("❌ Failed to send. Please try again.");
      }
    } catch (err) {
      console.error("Error sending feature request", err);
      setStatus("❌ Error sending request.");
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
          Suggest a Feature
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="feature"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              What would you like to see added?
            </label>
            <textarea
              id="feature"
              value={feature}
              onChange={(e) => setFeature(e.target.value)}
              required
              rows={3}
              className="mt-1 w-full px-3 py-2 rounded bg-white bg-opacity-50 dark:bg-gray-700 text-black dark:text-white border border-gray-300 dark:border-gray-600 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          <div>
            <label
              htmlFor="reason"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Why would this be helpful?
            </label>
            <textarea
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
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
                  <Lightbulb className="w-4 h-4 mr-2" /> Submit Feature Request
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
        className="inline-flex items-center text-yellow-500 hover:text-yellow-600 focus:outline-none"
      >
        <Lightbulb className="w-5 h-5 mr-0 md:mr-2" />
        <span className="hidden md:inline text-sm text-black dark:text-white">
          Feature Request
        </span>
      </button>

      {mounted && isOpen && createPortal(modalContent, document.body)}
    </>
  );
}
