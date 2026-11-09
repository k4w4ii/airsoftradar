import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import HomeView from "../../components/HomeView";
import { Shell } from "../../components/ui";
import Welcome from "../../components/Welcome";
import { hrefFor, isWelcome, parseCatalog } from "../../lib/catalog";
import { catalogSearch, getRates, getWelcome } from "../../lib/data";
import { CURRENCIES, DEFAULT_CURRENCY, isLocale, t } from "../../lib/i18n";

export async function generateMetadata({ params, searchParams }) {
  const { locale } = await params;
  const sp = await searchParams;
  const tr = t(locale);
  if (isWelcome(sp)) {
    return { title: tr.title, description: tr.description, alternates: { canonical: `/${locale}`, languages: { hu: "/hu", en: "/en" } } };
  }
  const p = parseCatalog(sp);
  // egyetlen kategória = saját kanonikus oldal (keresőknek); minden más szűrés a kategória-oldalra mutat
  const one = !p.q && p.cats.length === 1 ? p.cats[0] : null;
  return {
    title: one ? `${tr.cats[one]} | AirsoftHunter` : tr.title,
    description: tr.description,
    alternates: { canonical: `/${locale}?cat=${one || "weapons"}`, languages: { hu: "/hu", en: "/en" } },
  };
}

export default async function Home({ params, searchParams }) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  const sp = await searchParams;

  const jar = await cookies();
  const cur = jar.get("cur")?.value;
  const currency = CURRENCIES.includes(cur) ? cur : DEFAULT_CURRENCY[locale];
  const rates = await getRates();

  if (isWelcome(sp)) {
    const data = await getWelcome();
    return (
      <Shell locale={locale} currency={currency} path={`/${locale}`} hideSearch>
        <Welcome locale={locale} currency={currency} rates={rates} data={data} />
      </Shell>
    );
  }

  const query = parseCatalog(sp);
  const data = await catalogSearch(query, currency, rates);
  // pénznemváltáskor az árszűrő értéke más pénznemben lenne -> azt elhagyjuk
  const path = hrefFor(locale, { ...query, min: 0, max: 0 });

  return (
    <Shell locale={locale} currency={currency} query={query.q} path={path}>
      <HomeView locale={locale} currency={currency} rates={rates} data={data} params={query} />
    </Shell>
  );
}
