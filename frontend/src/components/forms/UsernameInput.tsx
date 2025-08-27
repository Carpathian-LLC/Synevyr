"use client";

import React, { FC, InputHTMLAttributes } from "react";

const UsernameInput: FC<InputHTMLAttributes<HTMLInputElement>> = ({
  className = "",
  ...props
}) => {
  return (
    <input
      {...props}
      type="text"
      className={`w-full text-sm px-4 py-2 bg-white bg-opacity-20 dark:bg-white dark:bg-opacity-10 backdrop-blur-sm rounded-xl border border-gray-600 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-white ${className}`}
    />
  );
};

export default UsernameInput;
