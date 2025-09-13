import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      {
        source: '/admin/:path*',
        destination: 'http://localhost:8000/admin/:path*',
      },
    ];
  },
};

export default nextConfig;
