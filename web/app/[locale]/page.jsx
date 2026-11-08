import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import HomeView from "../../components/HomeView";
import { Shell } from "../../components/ui";
import { getManufacturers, getRates, getStats, listProducts } from "../../lib/data";
import { CURRENCIES, DEFAULT_CURRENCY, isLocale, t } from "../../lib/i18n";

export async function generateMetadata({ params }) {
  const { locale } = await params;
  const tr = t(locale);
  return {
    title: tr.title,
    description: tr.description,
    alternates: { canonical: `/${locale}`, languages: { hu: "/hu", en: "/en" } },
  };
}

export default async function Home({ params, searchParams }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const sp = await searchParams;
  const pick = (k) => (typeof sp[k] === "string" ? sp[k] : "");
  const query = { q: pick("q"), mfr: pick("mfr"), stock: pick("stock"), sort: pick("sort") || "popular", page: pick("page") };

  const jar = await cookies();
  const cur = jar.get("cur")?.value;
  const currency = CURRENCIES.includes(cur) ? cur : DEFAULT_CURRENCY[locale];

  const [list, rates, stats, manufacturers] = await Promise.all([
    listProducts(query), getRates(), getStats(), getManufacturers(),
  ]);

  const qs = new URLSearchParams(Object.entries(query).filter(([, v]) => v && v !== "popular")).toString();
  return (
    <Shell locale={locale} currency={currency} query={query.q} path={`/${locale}${qs ? `?${qs}` : ""}`}>
      <HomeView locale={locale} currency={currency} rates={rates} stats={stats} list={list}
                manufacturers={manufacturers} params={query} />
    </Shell>
  );
}
