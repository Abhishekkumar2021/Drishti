/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  poweredByHeader: false,
  
  // Environment variables available at build time
  env: {
    NEXT_PUBLIC_DRISHTI_API_URL: process.env.NEXT_PUBLIC_DRISHTI_API_URL || "http://localhost:8000",
  },
};

export default nextConfig;
