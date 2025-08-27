// app/publications/[slug]/page.tsx
import { promises as fs } from "fs";
import path from "path";
import matter from "gray-matter";
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import GoBackButton from "@/components/GoBackButton";
import type { Metadata } from "next";

// Next.js 15+ now makes params a Promise<{ slug: string }>
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const fullPath = path.join(process.cwd(), "posts", `${slug}.md`);

  try {
    const fileContents = await fs.readFile(fullPath, "utf8");
    const { data } = matter(fileContents);
    return {
      title: data.title,
      description: data.excerpt,
      alternates: {
        canonical: `https://carpathian.ai/publications/${slug}`,
      },
    };
  } catch {
    return {};
  }
}

export default async function PublicationPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const fullPath = path.join(process.cwd(), "posts", `${slug}.md`);

  try {
    const fileContents = await fs.readFile(fullPath, "utf8");
    const { data, content } = matter(fileContents);

    return (
      <article className="max-w-4xl mx-auto py-16 px-6">
        <h1 className="text-4xl font-bold mb-4">{data.title}</h1>
        <p className="mb-8">{data.date}</p>
        <div className="prose lg:prose-lg dark:prose-invert">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
        <div className="mt-10">
          <GoBackButton />
        </div>
      </article>
    );
  } catch (error) {
    console.error("Error loading publication:", error);
    notFound();
  }
}
