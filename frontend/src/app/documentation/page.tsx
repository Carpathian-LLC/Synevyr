// app/documentation/page.tsx
import { Metadata } from "next";
import fs from "fs";
import path from "path";
import matter from "gray-matter";
import DeveloperHubClient from "./DocumentationHubClient";
import DocumentationsList from "./DocumentationList";

export const metadata: Metadata = {
  title: "Documentation | Open Technology ⚡︎ Limitless Possibilities",
  description:
    "Follow application updates, read documentation, or learn how to use our API. Explore Carpathian's documentation.",
        alternates: {
    canonical: "https://carpathian.ai/documentation",
  },
};

export type Documentation = {
  id: number;
  title: string;
  excerpt: string;
  date: string;
  slug: string;
  thumbnail: string;
};

function getDocumentation(): Documentation[] {
  // Use the correct directory relative to process.cwd()
  // process.cwd() is already /Users/samuelmalkasian/Development/Carpathian/frontend
  const docsDirectory = path.join(process.cwd(), "documentation");
  
  // Only include markdown files
  const fileNames = fs
    .readdirSync(docsDirectory)
    .filter((fileName) => fileName.endsWith(".md"));

  const documentation = fileNames.map((fileName, index) => {
    const fullPath = path.join(docsDirectory, fileName);
    const fileContents = fs.readFileSync(fullPath, "utf8");
    const { data } = matter(fileContents);

    return {
      id: index,
      title: data.title,
      excerpt: data.excerpt,
      date: data.date,
      slug: data.slug,
      thumbnail: data.thumbnail,
    };
  });

  // Sort by date descending
  documentation.sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  return documentation;
}

export default function DocumentationPage() {
  const documentation = getDocumentation();
  return (
    <>
      <DeveloperHubClient />
      <DocumentationsList documentation={documentation} />
    </>
  );
}
