"use client";

import React, { FC, InputHTMLAttributes, useState } from "react";
import { Eye, EyeOff } from "lucide-react";

const PasswordInput: FC<InputHTMLAttributes<HTMLInputElement>> = ({
  className = "",
  ...props
}) => {
  const [visible, setVisible] = useState(false);

  return (
    <div className="relative w-full">
      <input
        {...props}
        type={visible ? "text" : "password"}
        className={`w-full text-sm px-4 py-2 pr-10 bg-white bg-opacity-20 dark:bg-white dark:bg-opacity-10 backdrop-blur-sm rounded-xl border border-gray-600 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-white ${className}`}
      />
      <button
        type="button"
        onClick={() => setVisible((prev) => !prev)}
        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-white focus:outline-none"
        aria-label={visible ? "Hide password" : "Show password"}
        tabIndex={-1}
      >
        {visible ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
      </button>
    </div>
  );
};

export default PasswordInput;
