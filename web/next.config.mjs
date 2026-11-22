const config = {
  poweredByHeader: false,
  ...(process.env.NEXT_STANDALONE === "1" && { output: "standalone" }),
  async rewrites() {
    const apiOrigin = process.env.API_ORIGIN || "http://127.0.0.1:8000";
    return [{ source: "/api/:path*", destination: apiOrigin + "/api/:path*" }];
  },
};

export default config;
