// app/documentation/DocumentationsList.tsx
"use client";

import { motion } from "framer-motion";
import Image from "next/image";
import Link from "next/link";
import { Documentation } from "@/app/documentation/page";

type DocumentationsListProps = {
  documentation: Documentation[];
};

export default function DocumentationsList({
  documentation,
}: DocumentationsListProps) {
  return (
    <section className="py-20 bg-gray-100 text-gray-900 dark:bg-gray-900 dark:text-gray-100">
      <div className="max-w-6xl mx-auto px-6">
        <motion.h2
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 1 }}
          className="text-4xl font-bold text-center mb-12"
        >
          Newest Documentation
        </motion.h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {documentation.map((doc) => (
            <Link key={doc.id} href={`/documentation/${doc.slug}`} passHref>
              <motion.div
                whileHover={{
                  scale: 1.05,
                  boxShadow: "0 0 30px rgba(59,130,246,0.8)",
                }}
                transition={{ duration: 0.3 }}
                className="p-6 bg-slate-100 drop-shadow-xl dark:bg-gray-800 dark:bg-opacity-80 rounded-lg backdrop-blur-md border border-gray-200 dark:border-gray-700 cursor-pointer"
              >
                {doc.thumbnail && (
                  <div className="mb-4">
                    <Image
                      src={doc.thumbnail}
                      alt={doc.title}
                      width={300}
                      height={200}
                      className="object-cover rounded-md"
                    />
                  </div>
                )}
                <h3 className="text-2xl font-bold mb-2 text-blue-500 dark:text-blue-400">
                  {doc.title}
                </h3>
                <p className="text-sm mb-2 text-gray-500 dark:text-gray-400">
                  {doc.date}
                </p>
                <p className="mb-4">{doc.excerpt}</p>
              </motion.div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
