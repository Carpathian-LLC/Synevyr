// app/company/CompanyClient.tsx
"use client";

import { motion } from "framer-motion";

export default function Company() {
  return (
    <>
      {/* Hero Section with Video Background */}
      <section className="relative w-full h-[400px] overflow-hidden flex items-center justify-center">
        {/* Blurred video background */}
        <div className="absolute inset-0 z-0">
          <div className="w-full h-full backdrop-blur-sm">
            <video
              className="w-full h-full object-cover"
              src="/carpathian-company.mp4"
              autoPlay
              muted
              loop
              playsInline
            />
          </div>
        </div>

        {/* Light/Dark overlay for contrast */}
        <div className="absolute inset-0 pointer-events-none z-10">
          <div className="block dark:hidden w-full h-full bg-gray-900 bg-opacity-40" />
          <div className="hidden dark:block w-full h-full bg-black bg-opacity-85 mix-blend-multiply" />
        </div>

        {/* Foreground text content */}
        <div className="relative z-20 flex flex-col items-center justify-center text-center text-white max-w-4xl px-4">
          <h1 className="text-5xl md:text-6xl font-extrabold drop-shadow-2xl px-6 bg-clip-text text-transparent bg-gradient-to-r from-pink-300 to-pink-600">
            Synevyr — The Open Source CRM by Carpathian
          </h1>
          <p className="mt-6 text-xl max-w-3xl">
            Built to unify your business data, streamline operations, and provide powerful insights without the cost or complexity of traditional CRM platforms.
          </p>
        </div>
      </section>

      {/* About Content Section */}
      <section className="py-20 bg-gray-100 text-gray-900 dark:bg-gray-900 dark:text-gray-100">
        <div className="max-w-6xl mx-auto px-6 space-y-16">
          {/* Our Mission */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-4xl font-bold mb-4 border-b border-pink-500 pb-2">
              Our Mission
            </h2>
            <p className="text-lg leading-relaxed">
              Synevyr is an open-source CRM designed to empower businesses, teams, and individuals with complete control over their customer data and workflows.
            </p>
          </motion.div>

          {/* Our Vision */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-4xl font-bold mb-4 border-b border-pink-500 pb-2">
              Our Vision
            </h2>
            <p className="text-lg leading-relaxed">
              To create a transparent, extensible, and intelligent CRM platform that integrates seamlessly with your tools, grows with your needs, and remains free for everyone to use and improve.
            </p>
          </motion.div>

          {/* What Sets Us Apart */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-4xl font-bold mb-4 border-b border-pink-500 pb-2">
              What Sets Synevyr Apart
            </h2>
            <ul className="list-disc list-inside text-lg space-y-2">
              <li>
                <strong>Open Source Freedom:</strong> Fully transparent codebase that you can host, modify, and scale on your own terms.
              </li>
              <li>
                <strong>AI-Powered Insights:</strong> Built-in analytics and automation to help you understand your customers better.
              </li>
              <li>
                <strong>Seamless Integrations:</strong> Connect with your existing systems to unify your business operations.
              </li>
            </ul>
          </motion.div>

          {/* Our Journey */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-4xl font-bold mb-4 border-b border-pink-500 pb-2">
              Our Journey
            </h2>
            <p className="text-lg leading-relaxed">
              Synevyr was created by Carpathian as part of our commitment to open technology. From its first release, it was built to be intuitive, scalable, and ready for real-world business needs without sacrificing freedom or privacy.
            </p>
          </motion.div>

          {/* Who We Serve */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-4xl font-bold mb-4 border-b border-pink-500 pb-2">
              Who Uses Synevyr
            </h2>
            <p className="text-lg leading-relaxed">
              Startups, agencies, small businesses, nonprofits, and developers or anyone looking for a powerful yet flexible CRM they truly own.
            </p>
          </motion.div>
        </div>
      </section>

    </>
  );
}
