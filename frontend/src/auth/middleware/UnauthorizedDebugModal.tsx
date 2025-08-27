"use client";

import { useEffect } from "react";
import { fetchWithoutAuth } from "./fetchWithoutAuth";

interface Props {
  path: string;
  status: number;
  onClose: () => void;
}

export default function UnauthorizedDebugModal({ path, status, onClose }: Props) {
  useEffect(() => {
    console.warn(`Unauthorized request [${status}]: ${path}`);
  }, [path, status]);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 p-6 rounded-2xl shadow-xl border border-gray-300 dark:border-gray-700 max-w-lg w-full">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-red-600">Unauthorized Request</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-800 dark:text-gray-300 dark:hover:text-white"
          >
            ✕
          </button>
        </div>
        <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
          The server responded with a <strong>{status}</strong> error while calling:
        </p>
        <pre className="bg-gray-100 dark:bg-gray-900 text-xs p-3 rounded whitespace-pre-wrap break-all">
          {path}
        </pre>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-4">
          This is a DEBUG modal and ONLY present while Carpathian is in Beta Test. If you see this, please notify the server admin! 
        </p>
        <form
  onSubmit={async (e) => {
    e.preventDefault();
    const message = (e.currentTarget.elements.namedItem("message") as HTMLTextAreaElement).value;
    try {
      await fetchWithoutAuth("/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "",
          email: "",
          subject: "Unauthorized Debug Report",
          message: `User saw 401 on:\n${path}\nStatus: ${status}\n\nMessage:\n${message}`,
        }),
      });
      alert("✅ Thanks! The issue has been reported.");
      onClose();
    } catch (err) {
      console.error("Failed to send debug report", err);
      alert("❌ Failed to send the report.");
    }
  }}
  className="mt-4 space-y-3"
>
  <label className="block text-sm text-gray-600 dark:text-gray-400">
    Optional message or steps to reproduce:
  </label>
  <textarea
    name="message"
    rows={3}
    className="w-full px-3 py-2 rounded bg-white bg-opacity-50 dark:bg-gray-700 text-black dark:text-white border border-gray-300 dark:border-gray-600 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
    placeholder="What were you doing before this happened?"
  />
  <div className="text-right">
    <button
      type="submit"
      className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded transition"
    >
      Send Report
    </button>
  </div>
</form>

      </div>
    </div>
  );
}
