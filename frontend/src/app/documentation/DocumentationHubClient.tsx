// app/documentation/DocumentationHubClient.tsx
"use client";

import { motion } from "framer-motion";
import Link from "next/link";

export default function DeveloperHubClient() {
  return (
    <>
      {/* Hero Section with Video Background */}
      <section className="relative w-full h-screen overflow-hidden">
        {/* Light mode video */}
        <video
          className="absolute inset-0 w-full h-full object-cover block dark:hidden"
          src="/carpathian-dev-light.mp4"
          autoPlay
          muted
          loop
          playsInline
        />
        {/* Dark mode video */}
        <video
          className="absolute inset-0 w-full h-full object-cover hidden dark:block"
          src="/carpathian-dev-dark.mp4"
          autoPlay
          muted
          loop
          playsInline
        />
        {/* Dark overlay with mix-blend for improved contrast */}
        <div className="absolute inset-0 bg-black bg-opacity-50 mix-blend-multiply"></div>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.2 }}
          className="relative z-10 flex flex-col items-center justify-center h-full text-center px-4 text-white"
        >
          <h1 className="text-4xl md:text-5xl font-extrabold drop-shadow-2xl bg-clip-text text-transparent bg-gradient-to-r from-green-400 via-blue-500 to-indigo-600 dark:from-purple-500 dark:via-pink-500 dark:to-purple-700">
            Developer Tools & APIs
          </h1>
          <p className="mt-6 text-xl md:text-1xl max-w-lg">
            We&apos;re always looking for skilled developers to collaborate with.
            Reach out if you&apos;d like to develop a plugin or tool.
          </p>
        </motion.div>
      </section>

      {/* Partnership Section */}
      <section className="py-20 bg-gray-100 text-gray-900 dark:bg-gray-900 dark:text-gray-100">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 1 }}
            className="text-4xl font-bold mb-6"
          >
            Join the Carpathian Developer Community
          </motion.h2>
          <p className="text-xl mb-8 max-w-3xl mx-auto">
            Whether you&apos;re an experienced developer or just starting out,
            we invite you to partner with us. Developers creating open-source
            tools get free access to our servers!
          </p>
          <Link href="/contact" className="inline-block">
            <motion.button
              whileHover={{
                scale: 1.05,
                boxShadow: "0 0 30px rgba(66,153,225,0.9)",
              }}
              transition={{ duration: 0.3 }}
              className="mt-8 px-8 py-4 bg-blue-500 hover:bg-indigo-800 text-white font-bold rounded"
            >
              JOIN OUR COMMUNITY
            </motion.button>
          </Link>
        </div>
      </section>
    </>
  );
}
