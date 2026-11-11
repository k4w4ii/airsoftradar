import { imgSrc } from "../../../lib/links";
import { hrefFor, LEAVES, GROUP_IDS } from "../../../lib/catalog";
import { getRates, suggest } from "../../../lib/data";
import { CURRENCIES, DEFAULT_CURRENCY, isLocale, money, t } from "../../../lib/i18n";

// Keresési javaslatok gépelés közben (components/SearchBox.jsx). GET ?q=...&l=hu
export const dynamic = "force-dynamic";

const fold = (s) => String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");

export async function GET(req) {
  const url = new URL(req.url);
  const q = (url.searchParams.get("q") || "").trim().slice(0, 60);
  const locale = isLocale(url.searchParams.get("l")) ? url.searchParams.get("l") : "hu";
  const json = (body) => new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json", "Cache-Control": "private, max-age=120" },
  });
  if (q.length < 2) return json({ products: [], brands: [], cats: [] });

  const cookie = req.headers.get("cookie") || "";
  const cur = /(?:^|;\s*)cur=([A-Z]{3})/.exec(cookie)?.[1];
  const currency = CURRENCIES.includes(cur) ? cur : DEFAULT_CURRENCY[locale];
  const tr = t(locale);
  try {
    const [res, rates] = await Promise.all([suggest(q), getRates()]);
    const base = { q: "", cats: [], attrs: {}, plats: [], brands: [], min: 0, max: 0, stock: false };
    const fq = fold(q);
    const cats = [...GROUP_IDS, ...LEAVES].filter((c) => fold(tr.cats[c]).includes(fq)).slice(0, 3)
      .map((c) => ({ label: tr.cats[c], href: hrefFor(locale, { ...base, cats: [c] }) }));
    return json({
      products: res.products.map((p) => ({
        name: p.name, manufacturer: p.manufacturer, image: imgSrc(p.image_url),
        price: money(p.best_price_huf ?? p.min_price_any_huf, currency, rates, locale),
        shops: tr.shops(p.offer_count), href: `/${locale}/p/${p.slug}`,
      })),
      brands: res.brands.map((b) => ({ label: b.name, n: b.n, href: hrefFor(locale, { ...base, brands: [b.name] }) })),
      cats,
    });
  } catch {
    return json({ products: [], brands: [], cats: [] });
  }
}
