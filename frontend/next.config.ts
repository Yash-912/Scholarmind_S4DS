import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow images from HF Spaces and other sources
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**.hf.space" },
      { protocol: "https", hostname: "arxiv.org" },
    ],
  },
  // Environment variables available at build time
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:7860",
  },
};

export default nextConfig;
