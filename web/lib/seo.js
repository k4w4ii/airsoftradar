// Programmatic SEO: schema.org JSON-LD a termékoldalakra, márka-gyűjtőoldalak (slug, minimális méret), árelőzmény-elemzés.
// Tiszta függvények (szerveren és tesztben is).
import { SITE_NAME, SITE_URL } from "./site";
import { altLanguages } from "./i18n";

export const PAGE_CURRENCY = { hu: "HUF", en: "EUR", de: "EUR", pl: "PLN", cs: "CZK" };
export const COLLECTION_MIN = 3;            // ennél kevesebb termékből nem készül gyűjtőoldal (vékony tartalom)

const round = (v, cur) => (cur === "HUF" || cur === "CZK" ? Math.round(v) : Math.round(v * 100) / 100);

/** Product + AggregateOffer JSON-LD. A nagyon eltérő árú (is_outlier) ajánlatok nem számítanak bele.
 *  Ha van raktáron lévő ajánlat, csak azokból számol (InStock), különben az összesből (OutOfStock). */
export function productJsonLd({ product, offers, locale, rates }) {
  const cur = PAGE_CURRENCY[locale] || "EUR";
  const rate = cur === "HUF" ? 1 : Number(rates?.[cur]) || null;
  const clean = (offers || []).filter((o) => !o.is_outlier && o.price_huf != null);
  if (!clean.length || !rate) return null;
  const instock = clean.filter((o) => o.stock === "in_stock");
  const use = instock.length ? instock : clean;
  const prices = use.map((o) => Number(o.price_huf) / rate);
  const url = `${SITE_URL}/${locale}/p/${product.slug}`;
  const ld = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.name,
    url,
    ...(product.image_url && /^https:\/\//.test(product.image_url) ? { image: [product.image_url] } : {}),
    ...(product.manufacturer ? { brand: { "@type": "Brand", name: product.manufacturer } } : {}),
    ...(product.model_code ? { mpn: product.model_code, sku: product.model_code } : {}),
    offers: {
      "@type": "AggregateOffer",
      priceCurrency: cur,
      lowPrice: round(Math.min(...prices), cur),
      highPrice: round(Math.max(...prices), cur),
      offerCount: new Set(use.map((o) => o.shop_name || o.id)).size,
      availability: instock.length ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
      url,
    },
  };
  return ld;
}

/** Morzsamenü JSON-LD: Főoldal > kategória > termék. */
export function breadcrumbJsonLd(items) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((it, i) => ({ "@type": "ListItem", position: i + 1, name: it.name, item: SITE_URL + it.path })),
  };
}

/** <script> tartalom: a „</script>” ne zárhassa le idő előtt. */
export const ldJson = (obj) => JSON.stringify(obj).replace(/</g, "\\u003c");

/** Márkanév -> URL-szelet: „Specna Arms” -> „specna-arms”, „E&L” -> „e-l”, „Tokyo Marui” -> „tokyo-marui”. */
export function brandSlug(name) {
  return String(name || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60);
}

export const collectionPath = (locale, brand, cat) => `/${locale}/b/${brandSlug(brand)}${cat ? `/${cat}` : ""}`;

/** Árelőzmény-elemzés a termékoldalra: 30 napos legalacsonyabb és átlagár, és hogy a mostani ár valódi akció-e.
 *  points: [{ observed_on: "YYYY-MM-DD", min_huf }], now: a mostani legjobb ár (HUF). */
export function historyStats(points, now, today = new Date()) {
  const from = new Date(today.getTime() - 30 * 864e5).toISOString().slice(0, 10);
  const last = (points || []).filter((p) => p.observed_on >= from).map((p) => Number(p.min_huf)).filter((v) => v > 0);
  if (last.length < 5 || !(now > 0)) return null;           // kevés adatból nem mondunk ítéletet
  const low = Math.min(...last);
  const avg = last.reduce((a, b) => a + b, 0) / last.length;
  const diff = Math.round(((now - avg) / avg) * 100);
  const verdict = now <= low ? "low" : diff <= -5 ? "below" : diff >= 5 ? "above" : "near";
  return { low, avg, diff: Math.abs(diff), verdict, days: last.length };
}

/** Az utolsó N nap pontjai (dátum szerint). */
export function lastDays(points, days, today = new Date()) {
  const from = new Date(today.getTime() - days * 864e5).toISOString().slice(0, 10);
  return (points || []).filter((p) => p.observed_on >= from);
}

/** Kanonikus cím és indexelés a szűrt listákra:
 *  - keresés (q): noindex, follow (a belső keresési találatoldal nem kerül a Google-be);
 *  - egy márka (+ legfeljebb egy kategória, más szűrő nélkül): a márka-gyűjtőoldal a kanonikus;
 *  - egy kategória: saját kanonikus (lapozva is, a rendezés/nézet nem számít);
 *  - minden más szűrés: a kategória-oldal (vagy a fegyverek) a kanonikus. */
export function catalogMeta(locale, p, tr) {
  if (p.q) return { title: `„${p.q}” | AirsoftHunter`, description: tr.description, robots: { index: false, follow: true } };
  const extra = Object.keys(p.attrs).length || p.plats.length || p.min || p.max;
  if (p.brands.length === 1 && p.cats.length <= 1 && !extra) {
    const c = p.cats[0] || null;
    const path = (l) => collectionPath(l, p.brands[0], c);
    return { title: `${tr.collectionTitle(p.brands[0], c ? tr.cats[c] : null)} | AirsoftHunter`, description: tr.description,
             alternates: { canonical: path(locale), languages: altLanguages(path) } };
  }
  const one = p.cats.length === 1 ? p.cats[0] : null;
  const clean = one && !p.brands.length && !extra && !p.stock;
  const page = clean && p.page > 1 ? `&page=${p.page}` : "";
  return {
    title: one ? `${tr.cats[one]}${page ? ` – ${p.page}.` : ""} | AirsoftHunter` : tr.title,
    description: tr.description,
    alternates: { canonical: `/${locale}?cat=${one || "weapons"}${page}`,
                  languages: altLanguages((l) => `/${l}?cat=${one || "weapons"}${page}`) },
  };
}

export { SITE_NAME };

