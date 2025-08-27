"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { fetchWithAuth } from "@/auth/middleware/fetchWithAuth";

const codeSnippets: string[] = [
  "// Initializing self-destruct sequence…",
  `fetch(/delete-account\`, { method: "DELETE" });`,
  "// Prepping scripts to delete user data from all nodes",
  "await db.purgeUser(userId);",
  "// Cleaning up caches…",
  "// Preparing to remove backups…",
  "// Finalizing…",
  'console.log("self destruct authentication complete.");',
  'console.log("Awaiting user delete account action.")',
];

interface DeleteAccountModalProps {
  open: boolean;
  onClose: () => void;
}


export const DeleteAccountModal: React.FC<DeleteAccountModalProps> = ({
  open,
  onClose,
}) => {
  const router = useRouter();
  const [phase, setPhase] = useState<"input" | "code" | "ready" | "deleting">("input");
  const [input, setInput] = useState("");
  const [error, setError] = useState(false);
  const [lines, setLines] = useState<string[]>([]);
useEffect(() => {
  if (open) {
    setPhase("input");
    setInput("");
    setError(false);
    setLines([]);
  }
}, [open]);

  useEffect(() => {
    const lower = input.toLowerCase();
    setError(input.length > 0 && lower !== "run.exe");
  }, [input]);

  useEffect(() => {
    if (phase !== "code") return;
    setLines([]);
    codeSnippets.forEach((line, idx) => {
      setTimeout(() => {
        setLines((prev) => [...prev, line]);
      }, idx * 300);
    });
  }, [phase]);

  useEffect(() => {
  if (open) {
    document.body.style.overflow = "hidden";
  } else {
    document.body.style.overflow = "";
  }

  return () => {
    document.body.style.overflow = "";
  };
}, [open]);


  useEffect(() => {
    if (phase === "code" && lines.length === codeSnippets.length) {
      const t = setTimeout(() => setPhase("ready"), 500);
      return () => clearTimeout(t);
    }
  }, [phase, lines.length]);

  const handleRun = () => {
    if (input.toLowerCase() === "run.exe") {
      setPhase("code");
    }
  };

  const handleDelete = async () => {
    setPhase("deleting");
    try {
      const res = await fetchWithAuth(`/auth/delete-account`, {
        method: "DELETE",
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.message || "Failed to delete account");
      }
      setLines((prev) => [...prev, `Backend: ${data.message || JSON.stringify(data)}`]);
      router.push("/delete-account-goodbye");
    } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setLines((prev) => [...prev, `Error: ${message}`]);
        setPhase("ready");
      }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
      <div className="relative w-full max-w-xl font-mono text-red-500 bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-red-400 rounded-2xl shadow-xl">
        {/* Terminal Header */}
        <div className="p-6 pb-0">
          <pre className="text-sm leading-snug">
            &gt; initiate account self-destruct{"\n"}
            &gt; confirm by typing: RUN.EXE
          </pre>
        </div>

        {/* Console Output / Scrollable Content */}
        <div className="px-6 mt-2 h-[20rem] overflow-y-auto border-t border-red-400 pt-4">
          {phase === "input" && (
            <>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type here…"
                className={`w-full px-3 py-2 mb-2 rounded bg-white bg-opacity-30 dark:bg-gray-900 text-red-500 border ${
                  error ? "border-red-500" : "border-red-400"
                } placeholder-red-300 focus:outline-none focus:ring-2 focus:ring-red-500`}
              />
              {error && (
                <p className="text-red-600 text-sm">
                  Confirmation code must be RUN.EXE
                </p>
              )}
            </>
          )}

          {(phase === "code" || phase === "ready" || phase === "deleting") &&
            lines.map((l, i) => (
              <pre key={i} className="whitespace-pre-wrap m-0">
                {l}
              </pre>
            ))}
        </div>

        {/* Footer Actions */}
        <div className="border-t border-red-400 p-6 flex flex-col sm:flex-row justify-end gap-3 bg-transparent">
          {phase === "input" && (
            <>
              <button
                onClick={onClose}
                className="w-full sm:w-auto px-4 py-2 bg-gray-800 text-gray-200 rounded hover:bg-gray-700 transition"
              >
                Keep my account
              </button>
              <button
                onClick={handleRun}
                disabled={input.toLowerCase() !== "run.exe"}
                className={`w-full sm:w-auto px-6 py-2 rounded font-bold transition-colors duration-200 ${
                  input.toLowerCase() === "run.exe"
                    ? "bg-red-600 text-white hover:brightness-110"
                    : "bg-red-800 text-red-300 opacity-50 cursor-not-allowed"
                }`}
              >
                RUN.EXE
              </button>
            </>
          )}

          {phase === "ready" && (
            <>
              <button
                onClick={onClose}
                className="w-full sm:w-auto px-4 py-2 bg-gray-800 text-gray-200 rounded hover:bg-gray-700 transition"
              >
                Keep my account
              </button>
              <button
                onClick={handleDelete}
                className="w-full sm:w-auto px-6 py-2 bg-red-600 text-white rounded shadow-[0_0_10px_rgba(255,0,0,0.7)] hover:brightness-110 transition"
              >
                Yes, destroy everything
              </button>
            </>
          )}

          {phase === "deleting" && (
            <div className="w-full flex justify-center">
              <div className="w-8 h-8 border-4 border-transparent border-t-red-400 rounded-full animate-spin" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
