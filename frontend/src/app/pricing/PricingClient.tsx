// app/pricing/PricingClient.tsx
"use client";

import React from "react";
import { motion } from "framer-motion";
import Link from "next/link";

// ---------------------- PricingCard Component ----------------------
interface PricingCardProps {
  title: string;
  price: string;
  features: string[];
  buttonText?: string;
  onButtonClick?: () => void;
}

const PricingCard: React.FC<PricingCardProps> = ({
  title,
  price,
  features,
  buttonText,
  onButtonClick,
}) => {
  return (
    <motion.div
      whileHover={{ scale: 1.05, boxShadow: "0 0 30px rgba(0,163,196,0.8)" }}
      transition={{ duration: 0.3 }}
      className="p-8 bg-slate-100 drop-shadow-xl dark:bg-gray-800 dark:bg-opacity-80 rounded-lg backdrop-blur-md border border-gray-200 dark:border-gray-700"
    >
      <h3 className="text-2xl font-semibold text-zinc-800 dark:text-blue-500">
        {title}
      </h3>
      <p className="mt-2 text-xl font-bold text-gray-900 dark:text-white">
        {price}
      </p>
      <ul className="mt-4 space-y-1">
        {features.map((feature, idx) => (
          <li key={idx} className="text-gray-700 dark:text-gray-300">
            {feature}
          </li>
        ))}
      </ul>
      {buttonText && onButtonClick && (
        <button
          onClick={onButtonClick}
          className="mt-6 px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white font-bold rounded"
        >
          {buttonText}
        </button>
      )}
    </motion.div>
  );
};

// ---------------------- ServiceCard Component ----------------------
interface ServiceCardProps {
  title: string;
  details: string[];
}

const ServiceCard: React.FC<ServiceCardProps> = ({ title, details }) => {
  return (
    <motion.div
      whileHover={{ scale: 1.05, boxShadow: "0 0 30px rgba(0,163,196,0.8)" }}
      transition={{ duration: 0.3 }}
      className="p-8 bg-slate-100 drop-shadow-xl dark:bg-gray-800 dark:bg-opacity-80 rounded-lg backdrop-blur-md border border-gray-200 dark:border-gray-700"
    >
      <h3 className="text-2xl font-semibold text-zinc-800 dark:text-blue-500">
        {title}
      </h3>
      <ul className="mt-4 space-y-1">
        {details.map((detail, idx) => (
          <li key={idx} className="text-gray-700 dark:text-gray-300">
            {detail}
          </li>
        ))}
      </ul>
      <Link
        href="/contact"
        className="mt-6 inline-block px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white font-bold rounded"
      >
        Contact Us
      </Link>
    </motion.div>
  );
};

// ---------------------- Pricing Data ----------------------

// Virtual Machine (Cloud) Plans
const cloudPricingPlans = [
  {
    title: "Registered", // Free Tier – always basic specs
    price: "FREE",
    features: ["1 VM", "Intel i7", "1 vCPUs", "2GB RAM"],
  },
  {
    title: "Starter",
    price: "$30/month",
    features: ["2 VMs", "Intel i7", "2 vCPUs", "2GB RAM"],
  },
  {
    title: "Growth",
    price: "$60/month",
    features: ["3 VMs", "Intel i7", "Up to 2vCPUs", "Unlimited Upgrades"],
  },
  {
    title: "Professional",
    price: "$120/month",
    features: ["4 VMs", "Intel i7", "Up to 4vCPUs", "Unlimited Upgrades"],
  }, 
  {
    title: "Enterprise",
    price: "$550/month",
    features: [
      "8 VMs",
      "Intel i7, i9, Xeon",
      "Up to 16 vCPUs",
      "Up to 32GB RAM",
      "512GB SSD Storage",
      "Unlimited Bandwidth",
      "Dedicated Support",
    ],
  },
  {
    title: "Infinite",
    price: "$5500+/month",
    features: [
      "Unlimited VMs",
      "Intel i7, i9, Xeon",
      "Up to 8 vCPUs",
      "Up to 64GB RAM",
      "Up to 1TB SSD Storage",
      "Unlimited Bandwidth",
      "Priority 24/7 Support",
    ],
  },
];

// Dedicated (Physical) Server Plans
const dedicatedServerPlans = [
  {
    title: "Core",
    price: "$75 per instance",
    features: [
      "Processor: Intel i7",
      "16GB RAM",
      "1500MB Intel Integrated GPU",
      "128GB HDD Storage",
      "Gigabit Connectivity",
      "Remote Management",
    ],
  },
  {
    title: "Edge",
    price: "$150 per instance",
    features: [
      "Processor: Intel Xeon",
      "16GB RAM",
      "2GB Quadro K620",
      "1TB HDD Storage",
      "Gigabit Connectivity",
      "Remote Management",
    ],
  },
  {
    title: "Ultra",
    price: "$450 per instance",
    features: [
      "Processor: Intel i9",
      "64GB RAM",
      "8GB AMD Radeon Pro 5500M",
      "8GB AMD Radeon RX 6600 XT",
      "1TB SSD Storage",
      "Gigabit Connectivity",
      "Remote Management",
    ],
  },
];

const additionalServices = [
  {
    title: "Consultation",
    details: [
      "Cloud Strategy Consulting",
      "Infrastructure Assessment",
      "Migration Planning",
      "Optimization Advisory",
    ],
  },
  {
    title: "AI/ML Solutions",
    details: [
      "Model Development",
      "Data Analysis",
      "Deployment Support",
      "Ongoing Monitoring",
    ],
  },
];

// ---------------------- Main Pricing Page Component ----------------------
export default function Pricing() {
  const handleInfiniteClick = () => {
    window.location.href = "/contact";
  };

  return (
    <main className="bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white">
      {/* Hero Section */}
      <section className="py-20 px-6 md:px-12 lg:px-24 text-center">
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1 }}
          className="text-5xl md:text-6xl font-extrabold"
        >
          Pricing & Solutions
        </motion.h1>
        <p className="mt-6 text-lg">
          You can choose from a range of plans for virtual machines or dedicated
          server options.
        </p>
      </section>

      {/* Cloud Server Pricing Section */}
      <section className="py-20 px-6 md:px-12 lg:px-24">
        <div className="max-w-6xl mx-auto text-center">
          <motion.h2
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="text-4xl font-bold"
          >
            Cloud Server Pricing
          </motion.h2>
          <div className="mt-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {cloudPricingPlans.map((plan, idx) => (
              <PricingCard
                key={idx}
                title={plan.title}
                price={plan.price}
                features={plan.features}
                buttonText={
                  plan.title === "Infinite" ? "Contact Us" : undefined
                }
                onButtonClick={
                  plan.title === "Infinite" ? handleInfiniteClick : undefined
                }
              />
            ))}
          </div>
        </div>
      </section>

      {/* Dedicated (Physical) Server Pricing Section */}
      <section className="py-20 px-6 md:px-12 lg:px-24">
        <div className="max-w-6xl mx-auto text-center">
          <motion.h2
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="text-4xl font-bold"
          >
            Dedicated Server Pricing
          </motion.h2>
          <p className="mt-4 text-lg">
          Our dedicated server solutions are built for reliability and performance, 
          optimized hardware configurations to ensure seamless 
          operation for mission-critical applications.
          </p>
          <div className="mt-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {dedicatedServerPlans.map((plan, idx) => (
              <PricingCard
                key={idx}
                title={plan.title}
                price={plan.price}
                features={plan.features}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Additional Services Section */}
      <section className="py-20 px-6 md:px-12 lg:px-24">
        <div className="max-w-6xl mx-auto text-center">
          <motion.h2
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="text-4xl font-bold"
          >
            Additional Services
          </motion.h2>
          <p className="mt-4 text-lg">
            Enhance your infrastructure with expert security, strategic
            consultation, and advanced AI/ML solutions.
          </p>
          <div className="mt-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {additionalServices.map((service, idx) => (
              <ServiceCard
                key={idx}
                title={service.title}
                details={service.details}
              />
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
