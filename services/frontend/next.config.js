/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080",
    NEXT_PUBLIC_KEYCLOAK_URL:
      process.env.NEXT_PUBLIC_KEYCLOAK_URL || "http://localhost:8180",
    NEXT_PUBLIC_KEYCLOAK_REALM:
      process.env.NEXT_PUBLIC_KEYCLOAK_REALM || "nemo",
    NEXT_PUBLIC_KEYCLOAK_CLIENT_ID:
      process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID || "nemo-frontend",
  },
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${process.env.API_GATEWAY_URL || "http://localhost:8080"}/api/v1/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
