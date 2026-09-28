import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone mode for Docker
  output: 'standalone',
  // Static games live in public/games/<name>/index.html. beforeFiles keeps the [...slug] page from claiming the URL.
  async rewrites() {
    return {
      beforeFiles: [
        { source: '/games/:name', destination: '/games/:name/index.html' },
      ],
      afterFiles: [],
      fallback: [],
    };
  },
};

export default nextConfig;
