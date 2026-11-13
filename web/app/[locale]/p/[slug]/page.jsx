import { cookies } from "next/headers";
import Link from "next/link";
import { notFound } from "next/navigation";
import AlertBox from "../../../../components/AlertBox";
import ProductView from "../../../../components/ProductView";
import { Shell } from "../../../../components/ui";
import { brandStats, getHistory, getOffers, getProduct, getRates } from "../../../../lib/data";
import { altLanguages, CURRENCIES, DEFAULT_CURRENCY, isLocale, money, t } from "../../../../lib/i18n";
import { mailEnabled } from "../../../../lib/mail";
import { TOOLS, toolPath, toolText } from "../../../../lib/tools";
import ToolIcon from "../../../../components/tools/ToolIcon";
import { breadcrumbJsonLd, COLLECTION_MIN, collectionPath, ldJson, productJsonLd } from "../../../../lib/seo";

export async function generateMetadata({ params }) {
  const { locale, slug } = await params;
  const product = await getProduct(slug);
  if (!product) return { title: t(locale).notFound };
  const price = money(product.best_price_huf ?? product.min_price_any_huf, DEFAULT_CURRENCY[locale] || "EUR", await getRates(), locale);
  return {
    title: `${product.name} – ${price} | AirsoftHunter`,
    description: `${product.manufacturer} ${product.name}: ${t(locale).offersIntro(product.offer_count)}`,
    alternates: { canonical: `/${locale}/p/${slug}`, languages: altLanguages((l) => `/${l}/p/${slug}`) },
    openGraph: product.image_url ? { images: [product.image_url] } : undefined,
  };
}

const STATUSES = ["sent", "ok", "stopped", "stoppedAll", "bad", "limit", "off", "expired"];

export default async function ProductPage({ params, searchParams }) {
  const { locale, slug } = await params;
  if (!isLocale(locale)) notFound();
  const product = await getProduct(slug);
  if (!product) notFound();
  const sp = (await searchParams) || {};
  const status = STATUSES.includes(sp.alert) ? sp.alert : null;

  const jar = await cookies();
  const cur = jar.get("cur")?.value;
  const currency = CURRENCIES.includes(cur) ? cur : DEFAULT_CURRENCY[locale];
  const [offers, history, rates, stats] = await Promise.all([getOffers(product.id), getHistory(product.id), getRates(),
                                                             brandStats().catch(() => [])]);
  const tr = t(locale);
  const ld = productJsonLd({ product, offers, locale, rates });
  const inCat = stats.find((r) => r.manufacturer === product.manufacturer && r.category === product.category)?.n || 0;
  // a termékhez illő kalkulátor (BB → FPS/Joule, rugó/motor → rugóválasztó, henger/cső → térfogatarány, akku → LiPo)
  const sub = product.subtypes || "", nm = product.name.toLowerCase();
  const toolSlug = product.category === "acc_ammo" && sub.includes(",bbw=") ? "fps-joule-calculator"
    : /cylinder|henger|zylinder/.test(nm) || (product.category === "part_hopup" && sub.includes(",pt=barrel,")) ? "cylinder-volume-ratio"
    : sub.includes(",pt=spring,") || sub.includes(",pt=motor,") ? "spring-motor-calculator"
    : product.category === "acc_power" && sub.includes(",pk=battery,") ? "lipo-rof-calculator" : null;
  const tool = toolSlug ? TOOLS.find((t) => t.slug === toolSlug) : null;
  const brandLink = product.manufacturer && inCat >= COLLECTION_MIN ? (
    <p className="small"><Link href={collectionPath(locale, product.manufacturer, product.category)}>
      {tr.relatedBrand(product.manufacturer, tr.cats[product.category])} ({inCat}) →</Link></p>
  ) : null;
  const toolLink = tool ? (
    <p className="small tool-hint"><Link href={toolPath(locale, tool.slug)}><ToolIcon name={tool.icon} size={16} /> {toolText(tool.slug, locale).name} →</Link></p>
  ) : null;
  const related = brandLink || toolLink ? <>{brandLink}{toolLink}</> : null;
  const crumbs = breadcrumbJsonLd([
    { name: "AirsoftHunter", path: `/${locale}` },
    { name: tr.cats[product.category] || product.category, path: `/${locale}?cat=${product.category}` },
    { name: product.name, path: `/${locale}/p/${slug}` },
  ]);

  return (
    <Shell locale={locale} currency={currency} path={`/${locale}/p/${slug}`}>
      {ld ? <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: ldJson(ld) }} /> : null}
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: ldJson(crumbs) }} />
      <ProductView locale={locale} currency={currency} rates={rates} product={product} offers={offers} history={history}
                   related={related}
                   alert={mailEnabled() || status ? <AlertBox product={product} locale={locale} currency={currency} rates={rates} status={status} /> : null} />
    </Shell>
  );
}
