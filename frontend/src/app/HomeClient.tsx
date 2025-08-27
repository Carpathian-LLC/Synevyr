// app/synevyr/SynevyrClient.tsx
"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import Image from "next/image";

export default function HomeClient() {
  return (
    <>
      {/* Hero Section with Video Background */}
      <section className="relative w-full h-screen overflow-hidden">
        <video
          className="absolute inset-0 w-full h-full object-cover"
          src="/synevyr.mp4"
          autoPlay
          muted
          loop
          playsInline
        />
        {/* Dark overlay with a mix for readability */}
        <div className="absolute inset-0 bg-black bg-opacity-20 mix-blend-multiply"></div>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1 }}
          className="relative z-10 flex flex-col items-center justify-center h-full text-center px-4 text-white"
        >
          <h1 className="text-5xl md:text-6xl text-white font-extrabold drop-shadow-2xl">
            Meet <span className="text-emerald-400"> SYNEVYR</span>
          </h1>
          <p className="mt-4 text-xl max-w-2xl">
            A CRM and cloud Data Lake for marketers, designed to combine the art of
            marketing with the science of data.
          </p>
        </motion.div>
      </section>

      {/* CRM Section */}
      <section className="py-20 bg-zinc-100 dark:bg-gray-800">
        <div className="max-w-6xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          {/* Synevyr Logo Placeholder */}
          <div className="flex flex-col items-center justify-center">
            <Image
              src="/crm-interface-light.png"
              alt="synevyr Logo"
              width={500}
              height={300}
              className="w-100 h-auto dark:hidden"
            />
            <Image
              src="/crm-interface-dark.png"
              alt="synevyr Logo"
              width={500}
              height={300}
              className="w-100 h-auto hidden dark:block"
            />
          </div>
          {/* Synevyr Details */}
          <div className="p-8 text-black dark:text-white bg-white dark:bg-gray-700 rounded-lg backdrop-blur-md border border-gray-200 dark:border-gray-600 drop-shadow-xl">
            <h3 className="text-2xl font-semibold mb-2">
              Built for Marketers. Engineered for Growth.
            </h3>
            <p className="text-base leading-relaxed">
              Synevyr is a next generation CRM and full-scale marketing intelligence platform.
              We’ve designed it to centralize data from every touchpoint, ensuring seamless
              full-funnel tracking and real-time insights from every channel. With a dedicated
              data lake, you have total control over customer interactions, campaign performance,
              and conversion trends. Synevyr transforms raw data into actionable strategies,
              enabling smarter decision-making, optimized marketing efforts, and measurable growth.
            </p>
          </div>
        </div>
      </section>

      {/* Second CRM Section */}
      <section className="py-20 bg-zinc-100 dark:bg-gray-800">
        <div className="max-w-6xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          {/* Synevyr Details */}
          <div className="p-8 text-black dark:text-white bg-white dark:bg-gray-700 rounded-lg backdrop-blur-md border border-gray-200 dark:border-gray-600 drop-shadow-xl">
            <h3 className="text-2xl font-semibold mb-2">
              Software That Just Works.
            </h3>
            <p className="text-base leading-relaxed">
              We believe technology should feel natural and intuitive. Synevyr isn’t just a collection
              of features—it’s been designed by marketers to complement your workflow. It’s intuitive,
              beautifully crafted, and puts powerful insights right at your fingertips.
            </p>
          </div>
          {/* Synevyr Logo Placeholder */}
          <div className="flex flex-col items-center justify-center">
            <Image
              src="/synevyr-crm-light.png"
              alt="synevyr Logo"
              width={500}
              height={300}
              className="w-100 h-auto dark:hidden"
            />
            <Image
              src="/synevyr-crm-dark.png"
              alt="synevyr Logo"
              width={500}
              height={300}
              className="w-100 h-auto hidden dark:block"
            />
          </div>
        </div>
      </section>

      {/* Connect Section */}
      <section className="py-20 bg-zinc-100 dark:bg-gray-900 dark:text-gray-100">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 1 }}
            className="text-4xl font-bold mb-8"
          >
            Interested in Beta Testing?
          </motion.h2>
          <p className="text-lg mb-8">
            We’re looking for beta testers as we develop the platform. Fill out the contact form below and we’ll reach out when it’s time to join our first round.
          </p>
          <motion.button whileHover={{ scale: 1.05 }} transition={{ duration: 0.3 }}>
            <Link
              href="/contact"
              className="inline-block px-8 py-4 cta-button-light font-bold rounded"
            >
              Contact Us
            </Link>
          </motion.button>
        </div>
      </section>
    </>
  );
}
