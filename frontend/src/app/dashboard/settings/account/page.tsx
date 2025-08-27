"use client";

import React, { useState, useEffect } from "react";
import { DeleteAccountModal } from "@/components/DeleteAccountModal";
import { fetchWithAuth } from "@/auth/middleware/fetchWithAuth";

type AccountInfo = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  roles: string[];
  created_at: string;
};

export default function AccountPage() {
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [accountInfo, setAccountInfo] = useState<AccountInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        const res = await fetchWithAuth("/auth/whoami", {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        });
        if (!res.ok) {
          // try to parse JSON error, else fallback to text
          const errBody = await res.json().catch(() => null);
          setError(errBody?.error || `Error ${res.status}`);
          return;
        }
        const data: AccountInfo = await res.json();
        setAccountInfo(data);
      } catch (err) {
        console.error(err);
        setError("Network error");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

if (loading) return null;
  return (
    <>
      <div className="p-6 space-y-10">
       <h2 className="text-xl font-semibold text-black dark:text-white">
          Account Information
        </h2>

        {loading && (
          <p className="text-gray-500 dark:text-gray-400">Loading…</p>
        )}

        {error && (
          <p className="text-red-500 dark:text-red-400">{error}</p>
        )}

        {!loading && accountInfo && (
          <>
            <section className="mb-5">
              <div className="bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-300 dark:border-gray-700 rounded-2xl shadow-md p-6">
                <p>
                  <span className="font-medium text-black dark:text-white">
                    Current Role:
                  </span>{" "}
                  <span className="text-gray-600 dark:text-gray-400">
                    {accountInfo.roles}
                  </span>
                </p>
              </div>
            </section>
            <section className="mb-5">
              <div className="bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-300 dark:border-gray-700 rounded-2xl shadow-md p-6">
                <p>
                  <span className="font-medium text-black dark:text-white">
                    Username:
                  </span>{" "}
                  <span className="text-gray-600 dark:text-gray-400">
                    {accountInfo.username}
                  </span>
                </p>
              </div>
            </section>

            <section className="mb-5">
              <div className="bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-300 dark:border-gray-700 rounded-2xl shadow-md p-6">
                <p>
                  <span className="font-medium text-black dark:text-white">
                    Name:
                  </span>{" "}
                  <span className="text-gray-600 dark:text-gray-400">
                  {accountInfo.first_name} {accountInfo.last_name}
                  </span>
                </p>
              </div>
            </section>

            <section className="mb-5">
              <div className="bg-white bg-opacity-50 dark:bg-gray-800 dark:bg-opacity-50 backdrop-blur-sm border border-gray-300 dark:border-gray-700 rounded-2xl shadow-md p-6">
                <p>
                  <span className="font-medium text-black dark:text-white">
                    Email:
                  </span>{" "}
                  <span className="text-gray-600 dark:text-gray-400">
                  {accountInfo.email}
                  </span>
                </p>
              </div>
            </section>
          </>
        )}

        <section>
          <div className="border-t border-gray-300 dark:border-gray-700 mb-5" />
          <div className="mt-5">
          <p
            onClick={() => setShowDeleteModal(true)}
            className="text-red-500 font-medium cursor-pointer hover:underline"
          >
            Delete your account
          </p>
          </div>
        </section>
      </div>
      <DeleteAccountModal
        open={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
      />
    </>
  );
}
