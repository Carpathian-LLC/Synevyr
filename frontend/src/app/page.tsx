// app/home/page.tsx
import { Metadata } from "next";
import HomeClient from "./HomeClient";

export const metadata: Metadata = {
  // Enhanced title with primary keywords
  title: "Synevyr Home | Data Analytics and Marketing CRM",
  
  description: "Synevyr is an Open Source CRM and marketing management platform that uses machine learning and artificial intelligence to provide insights, track sales, and deliever custom reports.",
  
  // Author and publisher information
  authors: [{ name: "Synevyr" }],
  creator: "Synevyr",
  publisher: "Synevyr",
  
  
  // Canonical URL and alternates
  alternates: {
    canonical: "https://Synevyr.org/",
    languages: {
      "en-US": "https://Synevyr.org/",
    },
  },
  
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  
  // Additional structured data hints
  category: "Technology",
  
  // App-specific metadata
  applicationName: "Synevyr",
  referrer: "origin-when-cross-origin",
  
};

// Enhanced component with better SEO structure
export default function HomePage() {
  return (
    <>
      <HomeClient />
    </>
  );
}