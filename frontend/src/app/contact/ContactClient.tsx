// app/contact/ContactClient.tsx
"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Image from "next/image";

export default function Contact() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("");

  const handleSubmit = async (e: { preventDefault: () => void }) => {
    e.preventDefault();
    setStatus("Sending...");
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/contact`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          mode: "cors",
          body: JSON.stringify({ name, email, subject, message }),
        }
      );

      if (res.ok) {
        setStatus("Message sent successfully!");
        setName("");
        setEmail("");
        setSubject("");
        setMessage("");
      } else {
        setStatus("There was an error sending your message.");
      }
    } catch (error) {
      console.error("Error submitting form:", error);
      setStatus("There was an error sending your message.");
    }
  };

  return (
    <>
      {/* Header Section */}
      <section className="relative w-full h-[50vh] overflow-hidden">
        <Image
          src="/carpathian-contact.jpg"
          alt="Contact Background"
          fill
          priority
          className="object-cover"
        />
        {/* Darker overlay */}
        <div className="absolute inset-0 bg-black bg-opacity-50"></div>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1 }}
          className="relative z-10 flex flex-col items-center justify-center h-full text-center px-4 text-white"
        >
          <h1 className="text-5xl md:text-6xl font-extrabold drop-shadow-2xl">
            Get In Touch
          </h1>
          <p className="mt-4 text-xl max-w-2xl">
            We&apos;d love to hear from you. Whether you&apos;re looking for
            support, have questions about our services, or just want to say
            hello, drop us a message!
          </p>
        </motion.div>
      </section>

      {/* Contact Form Section */}
      <section className="py-20 bg-gray-100 text-gray-900 dark:bg-gray-900 dark:text-gray-100">
        <div className="max-w-4xl mx-auto px-6">
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 1 }}
            className="text-4xl font-bold text-center mb-12"
          >
            Contact Us
          </motion.h2>
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <input
                type="text"
                placeholder="Your Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-3 bg-slate-100 drop-shadow-xl dark:bg-gray-800 dark:bg-opacity-80 rounded-md border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
              <input
                type="email"
                placeholder="Your Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-slate-100 drop-shadow-xl dark:bg-gray-800 dark:bg-opacity-80 rounded-md border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <input
              type="text"
              placeholder="Subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full px-4 py-3 bg-slate-100 drop-shadow-xl dark:bg-gray-800 dark:bg-opacity-80 rounded-md border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <textarea
              placeholder="Your Message"
              rows={5}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="w-full px-4 py-3 bg-slate-100 drop-shadow-xl dark:bg-gray-800 dark:bg-opacity-80 rounded-md border border-gray-200 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            ></textarea>
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
          </form>
          {status && (
            <p className="mt-4 text-center text-lg text-blue-500">{status}</p>
          )}
        </div>
      </section>
    </>
  );
}
