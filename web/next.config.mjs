/** @type {import('next').NextConfig} */
const nextConfig = {
  // A főoldal a böngésző nyelve szerint /hu vagy /en (middleware nélkül)
  async redirects() {
    return [
      { source: "/", has: [{ type: "header", key: "accept-language", value: "hu.*" }], destination: "/hu", permanent: false },
      { source: "/", destination: "/en", permanent: false },
    ];
  },
};

export default nextConfig;
