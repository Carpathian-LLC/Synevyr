// app/publications/page.tsx
import { Metadata } from "next";
import fs from "fs";
import path from "path";
import matter from "gray-matter";
import PublicationsClient from "./PublicationsClient";

export const metadata: Metadata = {
  title: "News & Publications | Open Technology ⚡︎ Limitless Possibilities",
  description: "Explore Carpathian's news, research, and publications updates.",
      alternates: {
    canonical: "https://carpathian.ai/publications",
  },
};

// 1) Export the Publication type
export type Publication = {
  id: number;
  title: string;
  excerpt: string;
  date: string;
  slug: string;
  thumbnail: string;
};

// 2) Read the Markdown files from the `posts/` folder
function getPublications(): Publication[] {
  const postsDirectory = path.join(process.cwd(), "posts");
  const fileNames = fs.readdirSync(postsDirectory);

  const publications = fileNames.map((fileName, index) => {
    const fullPath = path.join(postsDirectory, fileName);
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
  publications.sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  return publications;
}

export default function PublicationsPage() {
  const publications = getPublications();
  return <PublicationsClient publications={publications} />;
}
