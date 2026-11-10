import { SITE_URL } from "../lib/site";

// Csak a Google keresője (és a hozzá tartozó segédrobotok) indexelhet; minden más robot ki van tiltva
// (AI-tanító robotok, egyéb keresők, SEO-szkennerek). A Google-Extended (a Google AI-tanítása) NINCS a listán, így az is tiltott.
// Új kereső engedélyezése: a nevét az ALLOWED listába (pl. "Bingbot").
const ALLOWED = [
  "Googlebot", "Googlebot-Image", "Googlebot-Video", "Googlebot-News", "Storebot-Google",
  "Google-InspectionTool",          // Search Console élő teszt
  "AdsBot-Google", "AdsBot-Google-Mobile", "Mediapartners-Google",   // AdSense
];
const PRIVATE = ["/go/", "/cur", "/theme", "/api/"];

export default function robots() {
  return {
    rules: [
      { userAgent: ALLOWED, allow: "/", disallow: PRIVATE },
      { userAgent: "*", disallow: "/" },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}
