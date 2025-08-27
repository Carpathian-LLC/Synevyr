"use client";

import React, { useState, useEffect } from "react";
import { fetchWithAuth } from "@/auth/middleware/fetchWithAuth";
import { motion } from "framer-motion";

interface Props {
  show: boolean;
  onClose: () => void;
}

const getPasswordErrors = (password: string): string[] => {
  const errs: string[] = [];
  if (password.length < 8) errs.push("≥8 chars");
  if (!/[A-Z]/.test(password)) errs.push("uppercase");
  if (!/[a-z]/.test(password)) errs.push("lowercase");
  if (!/\d/.test(password)) errs.push("digit");
  if (!/[!@#$%^&*()_+{}:<>?~`-]/.test(password)) errs.push("special");
  return errs;
};

export default function ChangePasswordModal({ show, onClose }: Props) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [verifyNewPassword, setVerifyNewPassword] = useState("");
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [errors, setErrors] = useState<{
    currentPassword?: string;
    newPassword?: string;
    verifyNewPassword?: string;
    general?: string;
  }>({});
  const [loading, setLoading] = useState(false);
  

  useEffect(() => {
    if (show) {
      setCurrentPassword("");
      setNewPassword("");
      setVerifyNewPassword("");
      setErrors({});
    }
  }, [show]);

  useEffect(() => {
    const pwErrs = getPasswordErrors(newPassword);
    setErrors(prev => {
      const next = { ...prev };
      if (pwErrs.length) next.newPassword = `Need: ${pwErrs.join(", ")}`;
      else delete next.newPassword;
      return next;
    });
  }, [newPassword]);

  useEffect(() => {
    setErrors(prev => {
      const next = { ...prev };
      if (
        newPassword &&
        verifyNewPassword &&
        newPassword !== verifyNewPassword
      ) {
        next.verifyNewPassword = "Don’t match";
      } else {
        delete next.verifyNewPassword;
      }
      return next;
    });
  }, [newPassword, verifyNewPassword]);

  const handleSubmit = async () => {
    setSuccessMessage(null);
    const fieldErrs: typeof errors = {};
    if (!currentPassword) fieldErrs.currentPassword = "Required";
    if (!newPassword) fieldErrs.newPassword = "Required";
    if (!verifyNewPassword) fieldErrs.verifyNewPassword = "Required";
    if (
      newPassword &&
      verifyNewPassword &&
      newPassword !== verifyNewPassword
    ) {
      fieldErrs.verifyNewPassword = "Don't match";
    }
    if (Object.keys(fieldErrs).length) {
      setErrors(prev => ({ ...prev, ...fieldErrs }));
      return;
    }

    setLoading(true);
    setErrors({});
    try {
      const res = await fetchWithAuth(
        "/auth/change-password",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            currentPassword,
            newPassword,
            verifyNewPassword,
          }),
        }
      );
      const data = await res.json();
      if (!res.ok) {
        const msg = data.message || "Error";
        const srv: typeof errors = {};
        if (msg.toLowerCase().includes("current"))
          srv.currentPassword = msg;
        else if (msg.toLowerCase().includes("match"))
          srv.verifyNewPassword = msg;
        else srv.general = msg;
        setErrors(srv);
      } else {
        setSuccessMessage(data.message || "Password changed successfully.");
        onClose();
      }
    } catch {
      setErrors({ general: "Network error. Try again." });
    } finally {
      setLoading(false);
    }
  };

  if (!show) return null;

  return (
    <motion.div
      className="fixed inset-0 z-50 bg-gray-50 dark:bg-gray-800 dark:bg-opacity-40 bg-opacity-50 backdrop-blur-sm flex items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div
        className="bg-gray-100 dark:bg-gray-900 bg-opacity-40 dark:bg-opacity-70 border border-gray-200 dark:border-gray-800 backdrop-blur-lg rounded-lg shadow-lg p-6 w-full max-w-md"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
      >
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 text-center mb-4">
          Change Password
        </h3>

        <div className="space-y-4">
          {/* Current Password */}
          <div>
            <label className="block text-sm text-gray-800 dark:text-gray-200 mb-1">
              Current Password
            </label>
            <input
              type="password"
              value={currentPassword}
              onChange={e => setCurrentPassword(e.target.value)}
              className={`w-full px-4 py-2 text-gray-800 dark:text-gray-200 rounded-lg bg-gray-700 bg-opacity-20 placeholder-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.currentPassword ? "border border-red-500" : "border border-transparent"
              }`}
            />
            {errors.currentPassword && (
              <p className="text-red-400 text-xs mt-1">{errors.currentPassword}</p>
            )}
          </div>

          {/* New Password */}
          <div>
            <label className="block text-sm text-gray-800 dark:text-gray-200 mb-1">
              New Password
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              className={`w-full px-4 py-2 text-gray-800 dark:text-gray-200 rounded-lg bg-gray-700 bg-opacity-20 placeholder-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.newPassword ? "border border-red-500" : "border border-transparent"
              }`}
            />
            {errors.newPassword && (
              <p className="text-red-400 text-xs mt-1">{errors.newPassword}</p>
            )}
          </div>

          {/* Verify New Password */}
          <div>
            <label className="block text-sm text-gray-800 dark:text-gray-200 mb-1">
              Verify New Password
            </label>
            <input
              type="password"
              value={verifyNewPassword}
              onChange={e => setVerifyNewPassword(e.target.value)}
              className={`w-full px-4 py-2 text-gray-800 dark:text-gray-200 rounded-lg bg-gray-700 bg-opacity-20 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.verifyNewPassword ? "border border-red-500" : "border border-transparent"
              }`}
            />
            {errors.verifyNewPassword && (
              <p className="text-red-500 text-xs mt-1">{errors.verifyNewPassword}</p>
            )}
          </div>
        </div>

        {errors.general && (
          <p className="text-red-500 text-sm mt-4 text-center">{errors.general}</p>
        )}
        {successMessage && (
          <p className="text-green-400 text-sm mt-4 text-center">{successMessage}</p>
        )}


        <div className="mt-6 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-800 text-white rounded-md"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-md disabled:opacity-50"
          >
            {loading ? "Saving…" : "Save"}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
