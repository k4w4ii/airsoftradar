import { getAllSlugs } from "../lib/data";
import { GROUP_IDS, LEAVES } from "../lib/catalog";
import { SITE_URL } from "../lib/site";
import { DOCS } from "../lib/legal";

export const dynamic = "force-dynamic"; // kérésre készül (fordításkor nem kell adatbázis-kapcsolat)

const both = (path) => ({ languages: { hu: `${SITE_URL}/hu${path}`, en: `${SITE_URL}/en${path}` } });

export default async function sitemap() {
  const cats = ["", ...[...GROUP_IDS.filter((g) => g !== "weapons"), ...LEAVES].map((c) => `?cat=${c}`)];
  const lists = cats.flatMap((c) => ["hu", "en"].map((l) => ({
    url: `${SITE_URL}/${l}${c}`, changeFrequency: "daily", priority: c ? 0.7 : 1, alternates: both(c),
  })));
  let products = [];
  try {
    products = await getAllSlugs();
  } catch {
    products = []; // ha az adatbázis épp nem elérhető, a lista-oldalak akkor is bekerülnek
  }
  const items = products.flatMap((p) => ["hu", "en"].map((l) => ({
    url: `${SITE_URL}/${l}/p/${p.slug}`, lastModified: p.updated_at ? new Date(p.updated_at) : undefined,
    changeFrequency: "daily", priority: 0.6, alternates: both(`/p/${p.slug}`),
  })));
  const legal = Object.values(DOCS).flatMap((d) => ["hu", "en"].map((l) => ({
    url: `${SITE_URL}/${l}/${d[l]}`, changeFrequency: "yearly", priority: 0.2,
    alternates: { languages: { hu: `${SITE_URL}/hu/${d.hu}`, en: `${SITE_URL}/en/${d.en}` } },
  })));
  return [...lists, ...legal, ...items];
}
