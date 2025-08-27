// app/sitemap.xml/route.ts
import fs from 'fs';
import path from 'path';
import { NextResponse } from 'next/server';

export async function GET() {
  const baseUrl = 'https://carpathian.ai';

  // Static routes
  const staticPaths = [
    '/',
    '/ai-ml',
    '/app-hosting',
    '/beta-test',
    '/cloud',
    '/company',
    '/contact',
    '/pricing',
    '/privacy',
    '/publications',
    '/security',
    '/software',
    '/synevyr',
    '/upgrade',
    '/web-hosting',
  ];

  // Source directories for dynamic content
  const publicationsDir = path.join(process.cwd(), 'posts');
  const docsDir = path.join(process.cwd(), 'documentation');

  const getMarkdownSlugs = (dir: string) => {
    try {
      return fs
        .readdirSync(dir)
        .filter((file) => file.endsWith('.md') || file.endsWith('.mdx'))
        .map((file) => file.replace(/\.mdx?$/, ''));
    } catch (err) {
      console.error(`Error reading ${dir}:`, err);
      return [];
    }
  };

  const publicationSlugs = getMarkdownSlugs(publicationsDir);
  const docSlugs = getMarkdownSlugs(docsDir);

  const publicationsPaths = publicationSlugs.map((slug) => `/publications/${slug}`);
  const docPaths = docSlugs.map((slug) => `/documentation/${slug}`);

  const allPaths = [...staticPaths, ...publicationsPaths, ...docPaths];

  const urls = allPaths
    .map((route) => {
      const isPublication = route.startsWith('/publications/');
      const isDoc = route.startsWith('/documentation/');
      const changefreq = isPublication ? 'weekly' : isDoc ? 'monthly' : 'weekly';
      const priority = isPublication ? 0.6 : isDoc ? 0.5 : 0.8;

      return `
  <url>
    <loc>${baseUrl}${route}</loc>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority}</priority>
  </url>`;
    })
    .join('');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${urls}
</urlset>`;

  return new NextResponse(xml, {
    headers: {
      'Content-Type': 'application/xml',
    },
  });
}
