/** @type {import('next').NextConfig} */
// Biztonsági fejlécek minden oldalra. A CSP szándékosan csak a beágyazást/űrlapokat korlátozza
// (a szkripteket nem), hogy az AdSense bekapcsolásakor se törjön el semmi.
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()" },
  { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains" },
  { key: "Content-Security-Policy", value: "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'" },
];

const nextConfig = {
  poweredByHeader: false,   // ne árulja el a „X-Powered-By: Next.js” fejléc a technológiát
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
  // A főoldal a böngésző (első) nyelve szerint /hu, /de, /pl, /cs (szlovákoknak is), egyébként /en (middleware nélkül)
  async redirects() {
    return [
      { source: "/", has: [{ type: "header", key: "accept-language", value: "hu.*" }], destination: "/hu", permanent: false },
      { source: "/", has: [{ type: "header", key: "accept-language", value: "de.*" }], destination: "/de", permanent: false },
      { source: "/", has: [{ type: "header", key: "accept-language", value: "pl.*" }], destination: "/pl", permanent: false },
      { source: "/", has: [{ type: "header", key: "accept-language", value: "(?:cs|sk).*" }], destination: "/cs", permanent: false },
      { source: "/", destination: "/en", permanent: false },
    ];
  },
};

export default nextConfig;
