/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow requests from custom hostnames (for Kubernetes ingress)
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: '*',
          },
        ],
      },
    ];
  },
}

module.exports = nextConfig

