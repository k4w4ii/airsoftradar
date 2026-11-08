import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import HomeView, { defaultCat } from "../../components/HomeView";
import { Shell } from "../../components/ui";
import { catalogSearch, getRates, getStats } from "../../lib/data";
import { CURRENCIES, DEFAULT_CURRENCY, isLocale, t, WEAPON_CATS } from "../../lib/i18n";

const CATS = ["all", "weapons", "other", ...WEAPON_CATS];
const SORTS = ["popular", "price", "price_desc", "name"];

export async function generateMetadata({ params, searchParams }) {
  const { locale } = await params;
  const sp = await searchParams;
  const tr = t(locale);
  const cat = typeof sp.cat === "string" && CATS.includes(sp.cat) ? sp.cat : null;
  return {
    title: cat && cat !== "weapons" ? `${tr.cats[cat]} | AirsoftRadar` : tr.title,
    description: tr.description,
    alternates: { canonical: `/${locale}${cat ? `?cat=${cat}` : ""}`, languages: { hu: "/hu", en: "/en" } },
  };
}

function parse(sp) {
  const one = (k) => (typeof sp[k] === "string" ? sp[k] : Array.isArray(sp[k]) ? sp[k][0] : "");
  const q = one("q").trim().slice(0, 60);
  const cat = CATS.includes(one("cat")) ? one("cat") : defaultCat(q);
  const brands = [].concat(sp.brand || []).filter((b) => typeof b === "string" && b).slice(0, 30);
  const num = (k) => Math.max(0, Math.round(Number(one(k)) || 0));
  let [min, max] = [num("min"), num("max")];
  if (min && max && min > max) [min, max] = [max, min];
  return { q, cat, brands, min, max, stock: one("stock") === "1", sort: SORTS.includes(one("sort")) ? one("sort") : "popular", page: Math.max(1, num("page")) };
}

export default async function Home({ params, searchParams }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const query = parse(await searchParams);

  const jar = await cookies();
  const cur = jar.get("cur")?.value;
  const currency = CURRENCIES.includes(cur) ? cur : DEFAULT_CURRENCY[locale];

  const rates = await getRates();
  const [data, stats] = await Promise.all([catalogSearch(query, currency, rates), getStats()]);

  const back = new URLSearchParams();
  if (query.q) back.set("q", query.q);
  if (query.cat !== defaultCat(query.q)) back.set("cat", query.cat);
  query.brands.forEach((b) => back.append("brand", b));
  if (query.stock) back.set("stock", "1");
  // pénznemváltáskor az árszűrő értéke más pénznemben lenne -> azt elhagyjuk
  const path = `/${locale}${back.toString() ? `?${back}` : ""}`;

  return (
    <Shell locale={locale} currency={currency} query={query.q} path={path}>
      <HomeView locale={locale} currency={currency} rates={rates} stats={stats} data={data} params={query} />
    </Shell>
  );
}
