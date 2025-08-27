// app/publications/PublicationsClient.tsx
"use client";

import Image from "next/image";
import PublicationsList from "@/components/PublicationsList";
import { Publication } from "./page";

interface PublicationsClientProps {
  publications: Publication[];
}

export default function PublicationsClient({ publications }: PublicationsClientProps) {
  return (
    <>
      {/* Hero Section */}
<section className="relative w-full h-[400px] overflow-hidden flex items-center justify-center">
  {/* Background image */}
  <div className="absolute inset-0 z-0">
    <Image
      src="/carpathian-publications.jpeg"
      alt="Publications"
      fill
      priority
      className="object-cover"
    />
  </div>

  {/* Light/Dark overlay */}
  <div className="absolute inset-0 pointer-events-none z-10">
    <div className="block dark:hidden w-full h-full bg-gray-800 bg-opacity-10" />
    <div className="hidden dark:block w-full h-full bg-black bg-opacity-80 mix-blend-multiply" />
  </div>

  {/* Foreground text content */}
  <div className="relative z-20 flex flex-col items-center justify-center text-center text-white max-w-4xl px-4">
    <h1 className="text-5xl md:text-6xl font-extrabold drop-shadow-2xl">
      Publications, News, and Updates
    </h1>
    <p className="mt-4 text-xl max-w-3xl">
      Explore our latest company updates, technical blogs, research insights, and more.
    </p>
  </div>
</section>


      {/* Publications List Section */}
      <PublicationsList publications={publications} />

      {/* (Optional) Subscription Section */}
    </>
  );
}
