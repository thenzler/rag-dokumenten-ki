/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Adjust this for production if needed
  images: {
    domains: ['storage.googleapis.com'],
  },
  // Fpr deployment on Cloud Run
  output: 'standalone',
};

module.exports = nextConfig;
