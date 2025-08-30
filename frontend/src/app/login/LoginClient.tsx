// app/login/LoginClient.tsx
"use client";

import React, { useState, useEffect, FormEvent } from "react";
import axios, { AxiosError } from "axios";
import Link from "next/link";
import { useRouter } from "next/navigation"; 
import { useAuth } from "@/auth/AuthContext"; 
import "@/styles/globals.css";
import PasswordInput from "@/components/forms/PasswordInput";


interface LoginFormData {
  username: string;
  password: string;
}

interface APIError {
  [key: string]: string; // Allows for specific field errors or a general error
}

const validateUsername = (username: string): boolean =>
  /^[a-zA-Z0-9_]{3,30}$/.test(username);

export default function LoginClient() {
  const [formData, setFormData] = useState<LoginFormData>({
    username: "",
    password: "",
  });
  const [errors, setErrors] = useState<APIError>({});
  const [loading, setLoading] = useState(false);
  const [touched, setTouched] = useState({
    username: false,
    password: false,
  });


  const auth = useAuth(); // Get auth context methods
  const router = useRouter(); // Get Next.js router

  // Live validation: only show errors for touched fields with content
  useEffect(() => {
    const newErrors: APIError = {};
    if (touched.username && formData.username && !validateUsername(formData.username)) {
      newErrors.username =
        "Invalid username. It must be 3-30 characters (letters, numbers, or underscores).";
    }
    // Only validate password if touched and then cleared, or on submit for empty.
    // The required attribute on input handles initial empty state.
    // This useEffect mainly catches invalid formats or already touched empty fields.
    if (touched.password && formData.password === "") {
       // This specific check might be redundant if submit validation is robust
       // newErrors.password = "Password cannot be empty.";
    }
    setErrors(prevErrors => ({...prevErrors, ...newErrors})); // Merge to keep general errors
  }, [formData.username, formData.password, touched]); // More specific dependencies

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    // Clear specific field error on change if it existed
    if (errors[e.target.name]) {
      setErrors(prev => {
        const newErrors = {...prev};
        delete newErrors[e.target.name];
        return newErrors;
      });
    }
    if (errors.general) { // Also clear general error on any change
        setErrors(prev => {
            const newErrors = {...prev};
            delete newErrors.general;
            return newErrors;
        });
    }
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    setTouched((prev) => ({ ...prev, [e.target.name]: true }));
    // Trigger validation for the blurred field
    const fieldName = e.target.name;
    const fieldValue = e.target.value;
    const newFieldErrors: APIError = {};

    if (fieldName === "username" && fieldValue && !validateUsername(fieldValue)) {
        newFieldErrors.username = "Invalid username. It must be 3-30 characters (letters, numbers, or underscores).";
    } else if (fieldName === "username" && validateUsername(fieldValue) && errors.username) {
        // Clear username error if now valid
        setErrors(prev => { const N = {...prev}; delete N.username; return N;});
    }

    if (fieldName === "password" && fieldValue === "") {
        // newFieldErrors.password = "Password cannot be empty."; // Usually handled by required or submit
    } else if (fieldName === "password" && fieldValue !== "" && errors.password) {
         setErrors(prev => { const N = {...prev}; delete N.password; return N;});
    }
    setErrors(prev => ({...prev, ...newFieldErrors}));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    // Mark all fields as touched to show any existing validation errors from useEffect/onBlur
    setTouched({ username: true, password: true });

    // Perform final validation check before submitting
    let currentSubmitErrors: APIError = {};
    if (!formData.username || !validateUsername(formData.username)) {
      currentSubmitErrors.username =
        "Invalid username. It must be 3-30 characters (letters, numbers, or underscores).";
    }
    if (!formData.password) {
      currentSubmitErrors.password = "Password cannot be empty.";
    }

    // Combine with any existing specific errors (e.g., from live validation)
    // but prioritize submit-time validation messages.
    currentSubmitErrors = {...errors, ...currentSubmitErrors};


    if (Object.keys(currentSubmitErrors).some(key => currentSubmitErrors[key])) {
      setErrors(currentSubmitErrors);
      return;
    }
    setErrors({}); // Clear errors before new API call

    setLoading(true);

    try {
      const res = await axios.post(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/login`,
        formData,
        { withCredentials: true }
      );
      const data = res.data as { // Define expected response structure
        success: boolean;
        message?: string; // Optional message from backend
        two_fa_required?: boolean;
        // access_token is not used client-side due to HttpOnly cookies
      };

      if (data.success) {
        await auth.checkAuthStatus(); // Update AuthContext
        router.push("/dashboard");    // Navigate using Next.js router
      } else if (data.success) {
      }  {
        // This case might be hit if backend returns success: false with a message
        setErrors({ general: data.message || "Login failed. Please try again." });
      }
    } catch (err: unknown) {
      const ae = err as AxiosError<{ errors?: Record<string, string>; message?: string }>;
      if (ae.response?.data?.errors) {
        setErrors(ae.response.data.errors);
      } else if (ae.response?.data?.message) { // Check for a general message from backend
        setErrors({ general: ae.response.data.message });
      }
      else {
        setErrors({
          general: "An unexpected error occurred. Please try again later.",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  // Determine if the submit button should be disabled
  // Disabled if loading, or if there are any active errors after fields have been touched.
  const isSubmitDisabled = loading || Object.values(errors).some(error => !!error);


  return (
    <>
      {/* Login Form Section */}
      <section className="py-16 bg-gradient-to-br from-white to-gray-200 dark:from-gray-800 dark:to-black">
        <div className="max-w-lg mx-auto bg-white dark:bg-gray-800 rounded-xl shadow-xl p-10">
            {/* Notification inside the login box */}
          
          <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-8">
            Log In
          </h2>

          {errors.general && (
            <p className="text-red-500 text-center mb-4">{errors.general}</p>
          )}

          <form onSubmit={handleSubmit} className="space-y-6" autoComplete="on">
            {/* Username Field */}
<div>
  <label
    htmlFor="username"
    className="block text-gray-700 dark:text-gray-300 mb-1"
  >
    Username
  </label>
  <input
    type="text"
    name="username"
    id="username"
    value={formData.username}
    onChange={handleChange}
    onBlur={handleBlur}
    autoComplete="username"
    required
    aria-invalid={!!errors.username}
    aria-describedby={errors.username ? "username-error" : undefined}
    className="w-full text-sm px-4 py-2 bg-white bg-opacity-20 dark:bg-white dark:bg-opacity-10 backdrop-blur-sm rounded-xl border border-gray-600 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-white"
  />
  {errors.username && (
    <p id="username-error" className="text-red-500 text-sm mt-1">{errors.username}</p>
  )}
</div>

            {/* Password Field */}
            <div>
              <label
                htmlFor="password"
                className="block text-gray-700 dark:text-gray-300"
              >
                Password
              </label>
              <PasswordInput
                name="password"
                id="password"
                value={formData.password}
                onChange={handleChange}
                onBlur={handleBlur}
                autoComplete="current-password"
                required
                aria-invalid={!!errors.password}
                aria-describedby={errors.password ? "password-error" : undefined}
                className="mt-1"
              />
              {errors.password && (
                <p id="password-error" className="text-red-500 text-sm mt-1">{errors.password}</p>
              )}
            </div>



            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitDisabled}
              className="w-full py-3 rounded-md font-semibold transition hover:opacity-90 bg-gradient-to-r from-sky-500 via-blue-500 to-purple-500 text-white disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? "Logging In..." : "Log In"}
            </button>
          </form>

          <p className="mt-6 text-center text-gray-700 dark:text-gray-300 text-lg">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="text-blue-500 hover:underline">
              Sign Up
            </Link>
          </p>
        </div>
      </section>
    </>
  );
}