// app/robots.txt/route.ts
import { NextResponse } from 'next/server'

export async function GET() {
  const content = `
User-agent: *
Disallow: /dashboard
Disallow: /console/
Disallow: /login
Disallow: /signup
Disallow: /delete-account-goodbye
Disallow: /thank-you
Disallow: /auth/
Disallow: cancel
Disallow: success
Allow: /

Sitemap: https://carpathian.ai/sitemap.xml
`.trim()

  return new NextResponse(content, {
    headers: {
      'Content-Type': 'text/plain',
    },
  })
}
