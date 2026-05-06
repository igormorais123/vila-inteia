import type { NextConfig } from "next";

const cfg: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/v1/politica/:path*",
        destination: process.env.VILA_API_BASE
          ? `${process.env.VILA_API_BASE}/api/v1/politica/:path*`
          : "http://localhost:8123/api/v1/politica/:path*",
      },
    ];
  },
};

export default cfg;
