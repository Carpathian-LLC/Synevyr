"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";

export type ContactField = {
  name: string;
  label?: string;
  type?: string;
  placeholder?: string;
  required?: boolean;
  textarea?: boolean;
};

type ContactFormProps = {
  fields?: ContactField[];
  endpoint?: string;
  redirectUrl?: string;
};

export default function ContactForm({
  fields = [
    { name: "name", placeholder: "Your Name", required: true },
    { name: "email", type: "email", placeholder: "Your Email", required: true },
    { name: "message", placeholder: "Your Message", required: true, textarea: true },
  ],
  endpoint = `${process.env.NEXT_PUBLIC_API_BASE_URL}/contact`,
  redirectUrl = "/thank-you",
}: ContactFormProps) {
  const router = useRouter();
  const [formState, setFormState] = useState<Record<string, string>>(
    Object.fromEntries(fields.map((field) => [field.name, ""]))
  );
  const [status, setStatus] = useState("");

  const handleChange = (name: string, value: string) => {
    setFormState((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("Sending...");

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        mode: "cors",
        body: JSON.stringify(formState),
      });

      if (res.ok) {
        router.push(redirectUrl);
      } else {
        setStatus("There was an error sending your message.");
      }
    } catch (err) {
      console.error(err);
      setStatus("There was an error sending your message.");
    }
  };

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {fields.map((field, index) => {
          const isTextArea = field.textarea;
          const commonProps = {
            name: field.name,
            value: formState[field.name] || "",
            onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
              handleChange(field.name, e.target.value),
            required: field.required ?? false,
            placeholder: field.placeholder || field.label || field.name,
            className:
              "w-full px-4 py-3 bg-slate-100 drop-shadow-xl dark:bg-gray-800 dark:bg-opacity-80 rounded-md border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500",
          };

          if (isTextArea) {
            return (
              <div key={index} className="md:col-span-2">
                <textarea rows={5} {...commonProps} />
              </div>
            );
          }

          return (
            <input
              key={index}
              type={field.type || "text"}
              {...commonProps}
              className={commonProps.className}
            />
          );
        })}
      </div>

      <motion.button
        type="submit"
        whileHover={{
          scale: 1.05,
          boxShadow: "0 0 30px rgba(59,130,246,0.8)",
        }}
        transition={{ duration: 0.3 }}
        className="w-full px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-bold rounded-md shadow-lg"
      >
        Send Message
      </motion.button>

      {status && <p className="mt-4 text-center text-lg text-blue-500">{status}</p>}
    </form>
  );
}
