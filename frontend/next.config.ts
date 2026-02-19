import type { NextConfig } from "next";
import withPWA from "@ducanh2912/next-pwa";

const nextConfig: NextConfig = {
  /* config options here */
};

const pwa = withPWA({
  dest: "public",
  register: true,
  disable: process.env.NODE_ENV === "development", // Only enable PWA in production
});

export default pwa(nextConfig);
