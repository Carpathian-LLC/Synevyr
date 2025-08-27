import type { NextConfig } from "next";
import withMDX from "@next/mdx";

const mdx = withMDX({
  extension: /\.mdx?$/,
  options: {},
});

const nextConfig: NextConfig = {
  pageExtensions: ["js", "jsx", "ts", "tsx", "md", "mdx"],
  images: {
    domains: ["carpathian.ai"],
  },
  async redirects() {
    return [
      {
        source: "/:path*",
        has: [{ type: "host", value: "www.carpathian.ai" }],
        destination: "https://carpathian.ai/:path*",
        permanent: true,
      },
    ];
  },
};

export default mdx(nextConfig);
