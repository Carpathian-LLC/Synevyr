// src/app/signup/page.tsx
"use client";

import React, { useState, useEffect, FormEvent, useMemo } from "react";
import axios, { AxiosError } from "axios";
import { useRouter } from "next/navigation";
import Link from "next/link";
import "@/styles/globals.css";
import { useSearchParams } from "next/navigation";
import UsernameInput from "@/components/forms/UsernameInput";
import PasswordInput from "@/components/forms/PasswordInput";


// Helper validation functions
const validateEmailFormat = (email: string): boolean =>
  /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/.test(email);

const validateUsername = (username: string): boolean =>
  /^[a-zA-Z0-9_]{3,30}$/.test(username);

const getPasswordErrors = (password: string): string[] => {
  const errors: string[] = [];
  if (password.length < 8) {
    errors.push("Password must be at least 8 characters long.");
  }
  if (!/[A-Z]/.test(password)) {
    errors.push("Password must contain at least one uppercase letter.");
  }
  if (!/[a-z]/.test(password)) {
    errors.push("Password must contain at least one lowercase letter.");
  }
  if (!/\d/.test(password)) {
    errors.push("Password must contain at least one digit.");
  }
  if (!/[!@#$%^&*()_+{}:<>?~`-]/.test(password)) {
    errors.push("Password must contain at least one special character.");
  }
  return errors;
};

interface SignupFormData {
  first_name: string;
  last_name: string;
  email: string;
  username: string;
  password: string;
  password_confirm: string;
  auth_code: string;
  referral_code?: string;
}

interface APIError {
  [key: string]: string;
}

const SignupPage: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const referralCode = useMemo(() => searchParams.get("ref") || undefined, [searchParams]);

  const [formData, setFormData] = useState<SignupFormData>({
    first_name: "",
    last_name: "",
    email: "",
    username: "",
    password: "",
    password_confirm: "",
    auth_code: "",
    referral_code: referralCode,
  });
  const [errors, setErrors] = useState<APIError>({});
  const [loading, setLoading] = useState(false);

  // Load saved form data (and referral code) from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("signupFormData");
    if (saved) {
      try {
        setFormData(prev => ({ ...prev, ...JSON.parse(saved) }));
      } catch {}
    }
    if (referralCode) {
      setFormData(prev => ({ ...prev, referral_code: referralCode }));
      localStorage.setItem("referralCode", referralCode);
    }
  }, [referralCode]);

  // Persist form data
  useEffect(() => {
    localStorage.setItem("signupFormData", JSON.stringify(formData));
  }, [formData]);

  // Live validation
  useEffect(() => {
    const newErrors: APIError = {};
    if (formData.email && !validateEmailFormat(formData.email)) {
      newErrors.email = "Invalid email format.";
    }
    if (formData.username && !validateUsername(formData.username)) {
      newErrors.username = 
        "Username must be 3–30 chars (letters, numbers, underscores).";
    }
    if (formData.password) {
      const pwErrs = getPasswordErrors(formData.password);
      if (pwErrs.length) newErrors.password = pwErrs.join("\n");
    }
    if (
      formData.password &&
      formData.password_confirm &&
      formData.password !== formData.password_confirm
    ) {
      newErrors.password_confirm = "Passwords do not match.";
    }
    setErrors(newErrors);
  }, [formData]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (Object.keys(errors).length > 0) return;
    setLoading(true);
    setErrors({});
    try {
      const resp = await axios.post(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/signup`,
        formData,
        { withCredentials: true }
      );
      if (resp.data.success) {
        localStorage.removeItem("signupFormData");
        router.push("/dashboard");
      }
    } catch (err: unknown) {
      const axiosErr = err as AxiosError<{ errors?: Record<string, string> }>;
      if (axiosErr.response?.data.errors) {
        setErrors(axiosErr.response.data.errors);
      } else {
        setErrors({ general: "Unexpected error—please try again later." });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="py-16 bg-gradient-to-br from-white to-gray-200 dark:from-gray-800 dark:to-black">
      <div className="max-w-lg mx-auto bg-white dark:bg-gray-800 rounded-xl shadow-xl p-10">
        <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-8">
          Sign Up
        </h2>
       <form onSubmit={handleSubmit} className="space-y-6" autoComplete="on">
          {/* First & Last Name */}
          <div>
            <label htmlFor="first_name" className="block mb-5 text-gray-700 dark:text-gray-300">
              First Name
            </label>
            <input
              id="first_name"
              name="first_name"
              autoComplete="given-name"
              value={formData.first_name}
              onChange={handleChange}
              required
              className="w-full text-sm px-4 py-2 bg-white bg-opacity-20 dark:bg-white dark:bg-opacity-10 backdrop-blur-sm rounded-xl border border-gray-600 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-white"
            />
          </div>
          <div>
            <label htmlFor="last_name" className="block mb-5 text-gray-700 dark:text-gray-300">
              Last Name
            </label>
            <input
              id="last_name"
              name="last_name"
              autoComplete="family-name"
              value={formData.last_name}
              onChange={handleChange}
              required
              className="w-full text-sm px-4 py-2 bg-white bg-opacity-20 dark:bg-white dark:bg-opacity-10 backdrop-blur-sm rounded-xl border border-gray-600 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-white"
            />
          </div>

          {/* Email */}
          <div>
            <label htmlFor="email" className="block mb-5 text-gray-700 dark:text-gray-300">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full text-sm px-4 py-2 bg-white bg-opacity-20 dark:bg-white dark:bg-opacity-10 backdrop-blur-sm rounded-xl border border-gray-600 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-white"
            />
            {errors.email && (
              <p className="text-red-500 text-sm mt-1 whitespace-pre-line">{errors.email}</p>
            )}
          </div>

          {/* Username */}
            <label htmlFor="username" className="block text-gray-700 dark:text-gray-300">
              Username
            </label>
            <UsernameInput
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              autoComplete="username"
            />
            {errors.username && (
              <p className="text-red-500 text-sm mt-1 whitespace-pre-line">{errors.username}</p>
            )}

          {/* Password & Confirmation */}
            <label htmlFor="password" className="block text-gray-700 dark:text-gray-300">
              Password
            </label>
            <PasswordInput
              id="password"
              name="password"
              autoComplete="new-password"
              value={formData.password}
              onChange={handleChange}
              required
            />
            {errors.password && (
              <p className="text-red-500 text-sm mt-1 whitespace-pre-line">{errors.password}</p>
            )}

            <label htmlFor="password_confirm" className="block text-gray-700 dark:text-gray-300">
              Confirm Password
            </label>
            <PasswordInput
              id="password_confirm"
              name="password_confirm"
              autoComplete="new-password"
              value={formData.password_confirm}
              onChange={handleChange}
              required
            />
            {errors.password_confirm && (
              <p className="text-red-500 text-sm mt-1 whitespace-pre-line">
                {errors.password_confirm}
              </p>
            )}


          <button
            type="submit"
            disabled={loading || Object.keys(errors).length > 0}
            className="w-full py-3 px-6 rounded-md font-semibold bg-blue-500 hover:bg-blue-600 text-white transition"
          >
            {loading ? "Signing Up..." : "Sign Up"}
          </button>
          {errors.auth_code && (
            <p className="text-red-500 text-sm mt-4 text-center">{errors.auth_code}</p>
          )}
        </form>

        <p className="mt-6 text-center text-gray-700 dark:text-gray-300 text-lg">
          Already have an account?{" "}
          <Link href="/login" className="text-blue-500 hover:underline">
            Log In
          </Link>
        </p>
        <a
          href="/beta-test"
          className="block text-sm text-center text-blue-600 hover:underline dark:text-blue-400"
        >
          Apply to beta test
        </a>
      </div>
    </section>
  );
};

export default SignupPage;
