import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import ProductView from "../../../../components/ProductView";
import { Shell } from "../../../../components/ui";
import { getHistory, getOffers, getProduct, getRates } from "../../../../lib/data";
import { CURRENCIES, DEFAULT_CURRENCY, isLocale, money, t } from "../../../../lib/i18n";

export async function generateMetadata({ params }) {
  const { locale, slug } = await params;
  const product = await getProduct(slug);
  if (!product) return { title: t(locale).notFound };
  const price = money(product.best_price_huf ?? product.min_price_any_huf, DEFAULT_CURRENCY[locale] || "EUR", await getRates(), locale);
  return {
    title: `${product.name} – ${price} | AirsoftHunter`,
    description: `${product.manufacturer} ${product.name}: ${t(locale).offersIntro(product.offer_count)}`,
    alternates: { canonical: `/${locale}/p/${slug}`, languages: { hu: `/hu/p/${slug}`, en: `/en/p/${slug}` } },
    openGraph: product.image_url ? { images: [product.image_url] } : undefined,
  };
}

export default async function ProductPage({ params }) {
  const { locale, slug } = await params;
  if (!isLocale(locale)) notFound();
  const product = await getProduct(slug);
  if (!product) notFound();

  const jar = await cookies();
  const cur = jar.get("cur")?.value;
  const currency = CURRENCIES.includes(cur) ? cur : DEFAULT_CURRENCY[locale];
  const [offers, history, rates] = await Promise.all([getOffers(product.id), getHistory(product.id), getRates()]);

  return (
    <Shell locale={locale} currency={currency} path={`/${locale}/p/${slug}`}>
      <ProductView locale={locale} currency={currency} rates={rates} product={product} offers={offers} history={history} />
    </Shell>
  );
}
