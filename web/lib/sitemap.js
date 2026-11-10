// Darabolt sitemap: /sitemap.xml = index, /sitemaps/static.xml (főoldal, kategóriák, jogi oldalak),
// /sitemaps/p-0.xml, p-1.xml … (termékek, fájlonként 10 000 termék = 20 000 URL; a Google-limit 50 000 / fájl).
import { countProducts, getAllSlugs } from "./data";
import { GROUP_IDS, LEAVES } from "./catalog";
import { DOCS } from "./legal";
import { SITE_URL } from "./site";

export const PER_FILE = 10000;
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

export function xmlResponse(body) {
  return new Response(`<?xml version="1.0" encoding="UTF-8"?>\n${body}`, {
    headers: { "Content-Type": "application/xml; charset=utf-8", "Cache-Control": "public, max-age=3600, s-maxage=3600" },
  });
}

function urlEntry(path, { lastmod, freq = "daily", prio = 0.6, pair } = {}) {
  const [hu, en] = pair || [`/hu${path}`, `/en${path}`];
  const alt = `<xhtml:link rel="alternate" hreflang="hu" href="${esc(SITE_URL + hu)}"/>` +
              `<xhtml:link rel="alternate" hreflang="en" href="${esc(SITE_URL + en)}"/>` +
              `<xhtml:link rel="alternate" hreflang="x-default" href="${esc(SITE_URL + en)}"/>`;
  return [hu, en].map((p) => `<url><loc>${esc(SITE_URL + p)}</loc>${lastmod ? `<lastmod>${lastmod}</lastmod>` : ""}` +
    `<changefreq>${freq}</changefreq><priority>${prio}</priority>${alt}</url>`).join("");
}

const urlset = (inner) =>
  `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">${inner}</urlset>`;

export function staticSitemap() {
  const cats = ["", ...[...GROUP_IDS, ...LEAVES].map((c) => `?cat=${c}`)];
  const lists = cats.map((c) => urlEntry(c, { prio: c ? 0.7 : 1 })).join("");
  const legal = Object.values(DOCS).map((d) => urlEntry("", { freq: "yearly", prio: 0.2, pair: [`/hu/${d.hu}`, `/en/${d.en}`] })).join("");
  return urlset(lists + legal);
}

export async function productSitemap(part) {
  const slice = await getAllSlugs(PER_FILE, part * PER_FILE);
  if (!slice.length) return null;
  return urlset(slice.map((p) => urlEntry(`/p/${p.slug}`, { lastmod: p.updated_at ? String(p.updated_at).slice(0, 10) : null })).join(""));
}

export async function sitemapIndex() {
  let n = 0;
  try { n = await countProducts(); } catch { n = 0; }
  const files = ["static", ...Array.from({ length: Math.ceil(n / PER_FILE) }, (_, i) => `p-${i}`)];
  const today = new Date().toISOString().slice(0, 10);
  return `<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">` +
    files.map((f) => `<sitemap><loc>${SITE_URL}/sitemaps/${f}.xml</loc><lastmod>${today}</lastmod></sitemap>`).join("") +
    `</sitemapindex>`;
}
