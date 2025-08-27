"use client";

import { motion } from "framer-motion";
import Image from "next/image";
import Link from "next/link";
import { Publication } from "../app/publications/page";

type PublicationsListProps = {
  publications: Publication[];
};

export default function PublicationsList({
  publications,
}: PublicationsListProps) {
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
          Latest Articles & Papers
        </motion.h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {publications.map((pub) => (
            <Link key={pub.id} href={`/publications/${pub.slug}`} passHref>
              <motion.div
                whileHover={{
                  scale: 1.05,
                  boxShadow: "0 0 30px rgba(59,130,246,0.8)",
                }}
                transition={{ duration: 0.3 }}
                className="p-6 bg-slate-100 drop-shadow-xl dark:bg-gray-800 dark:bg-opacity-80 rounded-lg backdrop-blur-md border border-gray-200 dark:border-gray-700 cursor-pointer"
              >
                {pub.thumbnail && (
                  <div className="mb-4">
                    <Image
                      src={pub.thumbnail}
                      alt={pub.title}
                      width={300}
                      height={200}
                      className="object-cover rounded-md"
                    />
                  </div>
                )}
                <h3 className="text-2xl font-bold mb-2 text-blue-500 dark:text-blue-400">
                  {pub.title}
                </h3>
                <p className="text-sm mb-2 text-gray-500 dark:text-gray-400">
                  {pub.date}
                </p>
                <p className="mb-4">{pub.excerpt}</p>
              </motion.div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
