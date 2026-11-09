import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import HomeView from "../../components/HomeView";
import { Shell } from "../../components/ui";
import { hrefFor, parseCatalog } from "../../lib/catalog";
import { catalogSearch, getRates } from "../../lib/data";
import { CURRENCIES, DEFAULT_CURRENCY, isLocale, t } from "../../lib/i18n";

export async function generateMetadata({ params, searchParams }) {
  const { locale } = await params;
  const p = parseCatalog(await searchParams);
  const tr = t(locale);
  // egyetlen kategória = saját kanonikus oldal (keresőknek); minden más szűrés a kategória-oldalra mutat
  const one = !p.q && p.cats.length === 1 && p.cats[0] !== "weapons" ? p.cats[0] : null;
  return {
    title: one ? `${tr.cats[one]} | AirsoftHunter` : tr.title,
    description: tr.description,
    alternates: { canonical: `/${locale}${one ? `?cat=${one}` : ""}`, languages: { hu: "/hu", en: "/en" } },
  };
}

export default async function Home({ params, searchParams }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const query = parseCatalog(await searchParams);

  const jar = await cookies();
  const cur = jar.get("cur")?.value;
  const currency = CURRENCIES.includes(cur) ? cur : DEFAULT_CURRENCY[locale];

  const rates = await getRates();
  const data = await catalogSearch(query, currency, rates);

  // pénznemváltáskor az árszűrő értéke más pénznemben lenne -> azt elhagyjuk
  const path = hrefFor(locale, { ...query, min: 0, max: 0, sort: "popular" });

  return (
    <Shell locale={locale} currency={currency} query={query.q} path={path}>
      <HomeView locale={locale} currency={currency} rates={rates} data={data} params={query} />
    </Shell>
  );
}
