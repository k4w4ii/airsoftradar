// Márka-gyűjtőoldalak (programmatic SEO): /hu/b/<márka> és /hu/b/<márka>/<kategória>, pl. /hu/b/cyma/rifle.
// Saját kanonikus cím, egyedi cím és bevezető szöveg (darabszám, raktáron, boltszám, legolcsóbb ár), a lista a katalóguséval azonos.
import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import HomeView from "./HomeView";
import { Shell } from "./ui";
import { CAT_GROUPS, GROUP_IDS, LEAVES } from "../lib/catalog";
import { brandStats, catalogSearch, collectionSummary, getRates } from "../lib/data";
import { CURRENCIES, DEFAULT_CURRENCY, isLocale, money, t } from "../lib/i18n";
import { brandSlug, COLLECTION_MIN, collectionPath } from "../lib/seo";

const leavesOf = (cat) => (!cat ? [] : CAT_GROUPS.find((g) => g.id === cat)?.leaves || [cat]);

async function resolve(locale, slug, cat) {
  if (!isLocale(locale) || (cat && !GROUP_IDS.includes(cat) && !LEAVES.includes(cat))) return null;
  const stats = await brandStats();
  const brand = stats.find((r) => brandSlug(r.manufacturer) === slug)?.manufacturer;
  if (!brand) return null;
  const sum = await collectionSummary(brand, leavesOf(cat));
  return sum.n ? { brand, sum } : null;
}

export async function collectionMetadata({ locale, brand: slug, cat }) {
  const r = await resolve(locale, slug, cat);
  if (!r) return { title: t(locale || "hu").notFound };
  const tr = t(locale);
  const title = tr.collectionTitle(r.brand, cat ? tr.cats[cat] : null);
  const low = r.sum.low ? money(r.sum.low, DEFAULT_CURRENCY[locale], await getRates(), locale) : null;
  const path = (l) => collectionPath(l, r.brand, cat);
  return {
    title: `${title} | AirsoftHunter`,
    description: tr.collectionIntro(r.sum.n, r.sum.inStock, r.sum.shops, low).trim(),
    alternates: { canonical: path(locale), languages: { hu: path("hu"), en: path("en") } },
    ...(r.sum.n < COLLECTION_MIN ? { robots: { index: false, follow: true } } : {}),
  };
}

export async function CollectionPage({ locale, brand: slug, cat, sp }) {
  const r = await resolve(locale, slug, cat);
  if (!r) notFound();
  const jar = await cookies();
  const c = jar.get("cur")?.value;
  const currency = CURRENCIES.includes(c) ? c : DEFAULT_CURRENCY[locale];
  const rates = await getRates();
  const tr = t(locale);
  const view = sp?.view === "list" ? "list" : "grid";
  // a „raktáron” a gyűjtőoldal alapja, ha van elég raktáron lévő termék
  const params = { q: "", cats: cat ? [cat] : [], attrs: {}, plats: [], brands: [r.brand], min: 0, max: 0,
                   stock: r.sum.inStock >= COLLECTION_MIN, sort: "discount", view, page: 1 };
  const data = await catalogSearch(params, currency, rates);
  const low = r.sum.low ? money(r.sum.low, currency, rates, locale) : null;
  return (
    <Shell locale={locale} currency={currency} path={collectionPath(locale, r.brand, cat)}>
      <HomeView locale={locale} currency={currency} rates={rates} data={data} params={params}
                title={tr.collectionTitle(r.brand, cat ? tr.cats[cat] : null)}
                intro={tr.collectionIntro(r.sum.n, r.sum.inStock, r.sum.shops, low)} />
    </Shell>
  );
}
