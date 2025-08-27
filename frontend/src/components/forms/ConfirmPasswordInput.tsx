"use client";

import React, { FC, useState, useEffect } from "react";
import { Eye, EyeOff } from "lucide-react";

interface ConfirmPasswordInputProps {
  onChange?: (password: string, confirm: string, match: boolean) => void;
  className?: string;
}

const ConfirmPasswordInput: FC<ConfirmPasswordInputProps> = ({
  onChange,
  className = "",
}) => {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [visible, setVisible] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const match = password === confirm && password.length > 0;
    setError(!match && confirm ? "Passwords do not match" : null);
    onChange?.(password, confirm, match);
  }, [password, confirm, onChange]);

  const inputClass =
    "w-full text-sm px-4 py-2 pr-10 bg-white bg-opacity-20 dark:bg-white dark:bg-opacity-10 backdrop-blur-sm rounded-xl border border-gray-600 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-white";

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="relative">
        <input
          type={visible ? "text" : "password"}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className={inputClass}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-white focus:outline-none"
          aria-label={visible ? "Hide password" : "Show password"}
          tabIndex={-1}
        >
          {visible ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
        </button>
      </div>

      <div className="relative">
        <input
          type={visible ? "text" : "password"}
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          placeholder="Confirm password"
          className={inputClass}
        />
      </div>

      {error && (
        <p className="text-sm text-red-500 dark:text-red-400">{error}</p>
      )}
    </div>
  );
};

export default ConfirmPasswordInput;
